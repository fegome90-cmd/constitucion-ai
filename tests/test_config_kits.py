"""Tests for config kits, exercised through their public seams."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES = REPO_ROOT / "templates"
APPLY_KIT = REPO_ROOT / "scripts" / "apply-kit.sh"
CHECK_VERSIONS = REPO_ROOT / "scripts" / "check-versions.sh"


@pytest.fixture
def version_root(tmp_path: Path) -> Path:
    """An independent example of the v2 contract with one exact pin."""
    root = tmp_path / "root"
    kit = root / "templates/python"
    starter = root / "starters/python"
    kit.mkdir(parents=True)
    starter.mkdir(parents=True)
    common = root / "templates/_common"
    common.mkdir()
    (common / "requirements-dev.txt").write_text("yamllint==1.2.3\n")
    (common / "package.json").write_text('{"devDependencies":{"markdownlint-cli2":"1.2.3"}}')
    (kit / "pyproject.toml").write_text('[dependency-groups]\ndev = ["ruff==1.2.3"]\n')
    (starter / "pyproject.toml").symlink_to("../../templates/python/pyproject.toml")
    (root / "catalog.json").write_text(
        json.dumps(
            {
                "templates": [
                    {
                        "id": "python",
                        "config_dir": "templates/python",
                        "starter_dir": "starters/python",
                        "pins": {
                            "file": "pyproject.toml",
                            "format": "pep440-exact",
                            "registry": "pypi",
                        },
                    }
                ]
            }
        )
    )
    for name in ("uv.lock", ".pre-commit-config.yaml"):
        shutil.copy2(REPO_ROOT / name, root / name)
    return root


def write_registry(destination: Path, **overrides: str) -> Path:
    registry = destination / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "ruff": "1.2.3",
                "mypy": "1.2.3",
                "yamllint": "1.2.3",
                "markdownlint-cli2": "1.2.3",
                **overrides,
            }
        )
    )
    return registry


def run_check_versions(
    registry_file: Path, root: Path | None = None
) -> subprocess.CompletedProcess[str]:
    command = ["bash", str(CHECK_VERSIONS)]
    if root is not None:
        command += ["--root", str(root)]
    command += ["--registry-file", str(registry_file)]
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def run_apply_kit(kit: str, destination: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(APPLY_KIT), kit, str(destination)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_python_kit_pins_core_tools_exactly() -> None:
    """The Python config kit carries exact, registry-sourced pins for its core tools."""
    pyproject = (TEMPLATES / "python" / "pyproject.toml").read_text()

    assert "hatchling==1.33.0" in pyproject
    assert "uv==0.13.9" in pyproject
    assert "ruff==0.17.5" in pyproject
    assert "mypy==2.4.1" in pyproject
    assert "pytest==9.2.0" in pyproject
    assert "[tool.ruff]" in pyproject
    assert "[tool.ruff.lint]" in pyproject
    assert "[tool.ruff.format]" in pyproject
    assert "[tool.mypy]" in pyproject
    assert "[tool.pytest.ini_options]" in pyproject


def test_common_kit_pins_cross_cutting_tools_exactly() -> None:
    """The shared kit pins every cross-cutting tool and keeps them separate from languages."""
    common = TEMPLATES / "_common"

    pins = (common / "requirements-dev.txt").read_text()
    assert "yamllint==1.38.0" in pins
    assert "shellcheck-py==0.11.0.1" in pins
    assert "codespell==2.4.3" in pins

    package = (common / "package.json").read_text()
    assert '"markdownlint-cli2": "0.24.1"' in package

    for config in (".markdownlint-cli2.jsonc", ".yamllint.yaml", ".shellcheckrc", ".codespellrc"):
        assert (common / config).is_file()


def test_catalog_declares_every_kit_and_its_two_layers() -> None:
    """The catalog is the single index of the ten kits and both of their layers."""
    catalog = json.loads((REPO_ROOT / "catalog.json").read_text())
    assert catalog["schema_version"] == 2
    assert len(catalog["templates"]) == 10
    for entry in catalog["templates"]:
        assert (REPO_ROOT / entry["config_dir"]).is_dir()
        assert (REPO_ROOT / entry["starter_dir"]).is_dir()
        assert set(entry["commands"]) == {
            "setup",
            "format",
            "lint",
            "typecheck",
            "test",
            "build",
            "dev",
            "check",
        }


def test_apply_kit_delivers_a_working_python_project(tmp_path: Path) -> None:
    """Applying the Python kit leaves a project whose generated config passes its smoke test."""
    result = run_apply_kit("python", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Smoke test Python: ruff format --check" in result.stdout
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    config = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert config["project"]["name"] == "python-config-kit-project"
    assert "readme" not in config["project"]
    assert "build-system" not in config
    assert "dev" in config["dependency-groups"]
    assert "ruff" in config["tool"]
    assert "mypy" in config["tool"]
    assert "pytest" in config["tool"]


def test_apply_kit_refuses_to_overwrite_existing_config(tmp_path: Path) -> None:
    """A destination that already carries config is left untouched."""
    sentinel = "config del usuario"
    (tmp_path / "pyproject.toml").write_text(sentinel)

    result = run_apply_kit("python", tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "pyproject.toml").read_text() == sentinel


def test_apply_kit_rejects_an_unknown_kit(tmp_path: Path) -> None:
    """An unknown kit fails clearly instead of copying an empty directory."""
    result = run_apply_kit("kotlin", tmp_path)

    assert result.returncode == 2
    assert "no existe el config kit" in result.stderr


def test_check_versions_rejects_drift(tmp_path: Path, version_root: Path) -> None:
    result = run_check_versions(write_registry(tmp_path, ruff="2.0.0"), root=version_root)

    assert result.returncode == 1
    assert "DRIFT python/ruff" in result.stdout


def test_precommit_revs_are_aligned_with_the_lockfile(tmp_path: Path, version_root: Path) -> None:
    result = run_check_versions(write_registry(tmp_path), root=version_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: revs de pre-commit alineados" in result.stdout


def test_check_versions_rejects_precommit_drift(tmp_path: Path, version_root: Path) -> None:
    precommit = version_root / ".pre-commit-config.yaml"
    precommit.write_text(precommit.read_text().replace("rev: v0.15.6", "rev: v0.0.1"))

    result = run_check_versions(write_registry(tmp_path), root=version_root)

    assert result.returncode == 1
    assert "PRE-COMMIT DRIFT ruff" in result.stdout


def test_check_versions_rejects_an_independently_declared_starter_pin(
    tmp_path: Path,
    version_root: Path,
) -> None:
    starter = version_root / "starters/python/pyproject.toml"
    content = starter.read_text()
    starter.unlink()
    starter.write_text(content)

    result = run_check_versions(write_registry(tmp_path), root=version_root)

    assert result.returncode == 1
    assert "DIVERGENTE python" in result.stdout


def test_current_manifest_matches_files() -> None:
    """The final integrity manifest describes the bytes actually in the repo."""
    lines = (REPO_ROOT / "MANIFEST.current.sha256").read_text().splitlines()
    assert lines
    for line in lines:
        expected, relative = line.split("  ", 1)
        path = REPO_ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, relative


@pytest.mark.parametrize("requirement", ["ruff>=1.2.3", "ruff<2", "ruff"])
def test_check_versions_rejects_a_minimum_instead_of_an_exact_pin(
    tmp_path: Path,
    version_root: Path,
    requirement: str,
) -> None:
    pyproject = version_root / "templates/python/pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace("ruff==1.2.3", requirement + '", "mypy==1.2.3')
    )

    result = run_check_versions(write_registry(tmp_path), root=version_root)

    assert result.returncode == 1
    assert f"PIN NO EXACTO python/{requirement}" in result.stdout


def test_check_versions_rejects_non_exact_build_system_pin(
    tmp_path: Path, version_root: Path
) -> None:
    pyproject = version_root / "templates/python/pyproject.toml"
    pyproject.write_text(
        '[build-system]\nrequires = ["hatchling>=1.33.0"]\n\n' + pyproject.read_text()
    )

    result = run_check_versions(write_registry(tmp_path), root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO python/hatchling>=1.33.0" in result.stdout


@pytest.mark.parametrize("kit", ["react", "typescript"])
def test_apply_kit_delivers_js_kit_without_docs_and_normalizes_name(
    tmp_path: Path, kit: str
) -> None:
    """Applying a JS/TS kit normalizes package.json name, skips docs, and passes its smoke test."""
    result = run_apply_kit(kit, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    package = json.loads((tmp_path / "package.json").read_text())
    assert package["name"] == f"{kit}-config-kit-project"
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    assert (tmp_path / "biome.json").is_file()
    assert (tmp_path / "tsconfig.json").is_file()


@pytest.mark.parametrize("kit", ["css", "playwright", "puppeteer", "react", "typescript"])
def test_apply_kit_refuses_to_overwrite_existing_package_json(tmp_path: Path, kit: str) -> None:
    """An existing JS/TS/CSS package.json is left untouched when applying a kit."""
    sentinel = '{"name": "existing-app"}\n'
    (tmp_path / "package.json").write_text(sentinel)

    result = run_apply_kit(kit, tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "package.json").read_text() == sentinel


def test_go_kit_pins_runtime_version_and_links_starter() -> None:
    """The Go config kit carries an exact go directive and is symlinked by the starter."""
    kit_mod = TEMPLATES / "go" / "go.mod"
    starter_mod = REPO_ROOT / "starters" / "go" / "go.mod"

    content = kit_mod.read_text()
    assert "module example.com/starter-go" in content
    assert "\ngo 1.23\n" in content
    assert starter_mod.is_symlink()
    assert not starter_mod.readlink().is_absolute()
    assert starter_mod.resolve() == kit_mod.resolve()


def test_apply_kit_delivers_a_working_go_project(tmp_path: Path) -> None:
    """Applying the Go kit normalizes module name, skips docs, and passes its smoke test."""
    result = run_apply_kit("go", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    go_mod = (tmp_path / "go.mod").read_text()
    assert "module example.com/go-config-kit-project" in go_mod
    assert "\ngo 1.23\n" in go_mod
    if shutil.which("go") is not None and shutil.which("gofmt") is not None:
        assert "Smoke test Go: gofmt" in result.stdout
        assert "Smoke test Go: go vet" in result.stdout
        assert "Smoke test Go: go test" in result.stdout
        assert "Smoke test Go: go build" in result.stdout


def test_apply_kit_refuses_to_overwrite_existing_go_mod(tmp_path: Path) -> None:
    """An existing go.mod is left untouched when applying the Go kit."""
    sentinel = "module example.com/existing\n\ngo 1.23\n"
    (tmp_path / "go.mod").write_text(sentinel)

    result = run_apply_kit("go", tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "go.mod").read_text() == sentinel


def test_check_versions_rejects_non_exact_go_version(tmp_path: Path, version_root: Path) -> None:
    """A range in templates/go/go.mod fails the exact-pin check."""
    go_kit = version_root / "templates/go"
    go_starter = version_root / "starters/go"
    go_kit.mkdir()
    go_starter.mkdir()
    (go_kit / "go.mod").write_text("module example.com/starter-go\n\ngo >=1.23\n")
    (go_starter / "go.mod").symlink_to("../../templates/go/go.mod")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "go",
            "config_dir": "templates/go",
            "starter_dir": "starters/go",
            "pins": {"file": "go.mod", "format": "gomod-version", "registry": "go"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    result = run_check_versions(write_registry(tmp_path, go="1.23"), root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO go/go: >=1.23" in result.stdout


def test_java_kit_pins_core_tools_exactly() -> None:
    """The Java config kit pins Maven plugins, JUnit, and google-java-format and links starter."""
    kit_pom = TEMPLATES / "java" / "pom.xml"
    starter_pom = REPO_ROOT / "starters" / "java" / "pom.xml"

    content = kit_pom.read_text()
    assert "<maven.compiler.release>21</maven.compiler.release>" in content
    assert "<junit.version>6.0.0</junit.version>" in content
    assert "<version>3.14.1</version>" in content
    assert "<version>3.5.4</version>" in content
    assert "<version>3.10.3</version>" in content
    assert "<version>2.0.0</version>" in content
    assert starter_pom.is_symlink()
    assert not starter_pom.readlink().is_absolute()
    assert starter_pom.resolve() == kit_pom.resolve()


def test_apply_kit_delivers_a_working_java_project(tmp_path: Path) -> None:
    """Applying the Java kit normalizes artifactId, skips docs, and passes its smoke test."""
    result = run_apply_kit("java", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    pom = (tmp_path / "pom.xml").read_text()
    assert "<artifactId>java-config-kit-project</artifactId>" in pom
    assert "<junit.version>6.0.0</junit.version>" in pom
    if shutil.which("mvn") is not None and shutil.which("java") is not None:
        assert "Smoke test Java: spotless:check verify" in result.stdout


def test_apply_kit_refuses_to_overwrite_existing_pom_xml(tmp_path: Path) -> None:
    """An existing pom.xml is left untouched when applying the Java kit."""
    sentinel = "<project><artifactId>existing</artifactId></project>\n"
    (tmp_path / "pom.xml").write_text(sentinel)

    result = run_apply_kit("java", tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "pom.xml").read_text() == sentinel


def test_check_versions_rejects_non_exact_java_pin(tmp_path: Path, version_root: Path) -> None:
    """A Maven version range in templates/java/pom.xml fails the exact-pin check."""
    java_kit = version_root / "templates/java"
    java_starter = version_root / "starters/java"
    java_kit.mkdir()
    java_starter.mkdir()
    pom_text = (TEMPLATES / "java" / "pom.xml").read_text()
    (java_kit / "pom.xml").write_text(
        pom_text.replace(
            "<junit.version>6.0.0</junit.version>", "<junit.version>[6.0.0,7.0.0)</junit.version>"
        )
    )
    (java_starter / "pom.xml").symlink_to("../../templates/java/pom.xml")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "java",
            "config_dir": "templates/java",
            "starter_dir": "starters/java",
            "pins": {"file": "pom.xml", "format": "maven-properties", "registry": "maven"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    registry = write_registry(
        tmp_path,
        junit="6.0.0",
        spotless="3.10.3",
        compiler="3.14.1",
        surefire="3.5.4",
        **{"google-java-format": "2.0.0"},
    )
    result = run_check_versions(registry, root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO java/junit: [6.0.0,7.0.0)" in result.stdout


def test_rust_kit_pins_toolchain_exactly_and_links_starter() -> None:
    """The Rust config kit pins channel, components, and edition, and starter symlinks them."""
    kit_toolchain = TEMPLATES / "rust" / "rust-toolchain.toml"
    kit_cargo = TEMPLATES / "rust" / "Cargo.toml"
    starter_toolchain = REPO_ROOT / "starters" / "rust" / "rust-toolchain.toml"
    starter_cargo = REPO_ROOT / "starters" / "rust" / "Cargo.toml"

    toolchain = tomllib.loads(kit_toolchain.read_text())
    assert toolchain["toolchain"]["channel"] == "1.100.0"
    assert toolchain["toolchain"]["components"] == ["rustfmt", "clippy"]
    assert toolchain["toolchain"]["profile"] == "minimal"

    cargo = tomllib.loads(kit_cargo.read_text())
    assert cargo["package"]["name"] == "starter-rust"
    assert cargo["package"]["edition"] == "2024"
    assert cargo["package"]["rust-version"] == "1.85"

    for starter_file, kit_file in (
        (starter_toolchain, kit_toolchain),
        (starter_cargo, kit_cargo),
    ):
        assert starter_file.is_symlink()
        assert not starter_file.readlink().is_absolute()
        assert starter_file.resolve() == kit_file.resolve()


def test_apply_kit_delivers_a_working_rust_project(tmp_path: Path) -> None:
    """Applying the Rust kit normalizes Cargo.toml name, skips docs, and passes its smoke test."""
    result = run_apply_kit("rust", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    cargo = tomllib.loads((tmp_path / "Cargo.toml").read_text())
    assert cargo["package"]["name"] == "rust-config-kit-project"
    toolchain = tomllib.loads((tmp_path / "rust-toolchain.toml").read_text())
    assert toolchain["toolchain"]["channel"] == "1.100.0"

    has_cargo = (Path.home() / ".cargo/bin/cargo").exists() or shutil.which("cargo") is not None
    has_rustc = (Path.home() / ".cargo/bin/rustc").exists() or shutil.which("rustc") is not None
    if has_cargo and has_rustc:
        assert "Smoke test Rust: cargo fmt --check" in result.stdout
        assert "Smoke test Rust: cargo clippy" in result.stdout
        assert "Smoke test Rust: cargo test" in result.stdout
        assert "Smoke test Rust: cargo build" in result.stdout


def test_apply_kit_refuses_to_overwrite_existing_cargo_toml(tmp_path: Path) -> None:
    """An existing Cargo.toml is left untouched when applying the Rust kit."""
    sentinel = '[package]\nname = "existing"\nversion = "0.1.0"\n'
    (tmp_path / "Cargo.toml").write_text(sentinel)

    result = run_apply_kit("rust", tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "Cargo.toml").read_text() == sentinel


def test_check_versions_rejects_non_exact_rust_channel(tmp_path: Path, version_root: Path) -> None:
    """A floating rustup channel like 'stable' fails the exact-pin check."""
    rust_kit = version_root / "templates/rust"
    rust_starter = version_root / "starters/rust"
    rust_kit.mkdir()
    rust_starter.mkdir()
    (rust_kit / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "stable"\n')
    (rust_starter / "rust-toolchain.toml").symlink_to("../../templates/rust/rust-toolchain.toml")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "rust",
            "config_dir": "templates/rust",
            "starter_dir": "starters/rust",
            "pins": {
                "file": "rust-toolchain.toml",
                "format": "rustup-channel",
                "registry": "rustup",
            },
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    result = run_check_versions(write_registry(tmp_path, rust="1.100.0"), root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO rust/rust: stable" in result.stdout


def test_css_kit_pins_core_tools_exactly() -> None:
    """The CSS config kit pins core tools exactly and shares config with its starter."""
    kit_pkg = TEMPLATES / "css" / "package.json"
    kit_biome = TEMPLATES / "css" / "biome.json"
    starter_pkg = REPO_ROOT / "starters" / "css" / "package.json"
    starter_biome = REPO_ROOT / "starters" / "css" / "biome.json"

    pkg = json.loads(kit_pkg.read_text())
    assert pkg["packageManager"] == "pnpm@12.18.0"
    assert pkg["devDependencies"]["@biomejs/biome"] == "2.6.8"
    assert pkg["devDependencies"]["vite"] == "8.3.8"

    biome = json.loads(kit_biome.read_text())
    assert biome["css"] == {"formatter": {"enabled": True}, "linter": {"enabled": True}}

    assert starter_pkg.is_symlink()
    assert not starter_pkg.readlink().is_absolute()
    assert starter_pkg.resolve() == kit_pkg.resolve()
    assert starter_biome.read_bytes() == kit_biome.read_bytes()


def test_apply_kit_delivers_a_working_css_project(tmp_path: Path) -> None:
    """Applying the CSS kit normalizes package.json name, skips docs, and passes its smoke test."""
    result = run_apply_kit("css", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    pkg = json.loads((tmp_path / "package.json").read_text())
    assert pkg["name"] == "css-config-kit-project"
    assert (tmp_path / "biome.json").is_file()

    if (REPO_ROOT / "starters/css/node_modules").is_dir():
        assert "Smoke test CSS: biome check" in result.stdout
        assert "Smoke test CSS: node --test" in result.stdout
        assert "Smoke test CSS: vite build" in result.stdout


def test_check_versions_rejects_non_exact_css_pin(tmp_path: Path, version_root: Path) -> None:
    """A caret npm range like '^8.3.8' in css/package.json fails the exact-pin check."""
    css_kit = version_root / "templates/css"
    css_starter = version_root / "starters/css"
    css_kit.mkdir()
    css_starter.mkdir()
    (css_kit / "package.json").write_text(
        json.dumps(
            {
                "name": "starter-css",
                "packageManager": "pnpm@12.18.0",
                "devDependencies": {"@biomejs/biome": "2.6.8", "vite": "^8.3.8"},
            }
        )
    )
    (css_starter / "package.json").symlink_to("../../templates/css/package.json")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "css",
            "config_dir": "templates/css",
            "starter_dir": "starters/css",
            "pins": {"file": "package.json", "format": "npm-exact", "registry": "npm"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    registry = write_registry(
        tmp_path,
        pnpm="12.18.0",
        vite="8.3.8",
        **{"@biomejs/biome": "2.6.8"},
    )
    result = run_check_versions(registry, root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO css/vite: ^8.3.8" in result.stdout


def test_playwright_kit_pins_core_tools_exactly() -> None:
    """The Playwright config kit pins core tools exactly and shares config with its starter."""
    kit_dir = TEMPLATES / "playwright"
    starter_dir = REPO_ROOT / "starters" / "playwright"

    pkg = json.loads((kit_dir / "package.json").read_text())
    assert pkg["packageManager"] == "pnpm@12.18.0"
    assert pkg["devDependencies"]["@playwright/test"] == "1.65.1"
    assert pkg["devDependencies"]["@biomejs/biome"] == "2.6.8"
    assert pkg["devDependencies"]["typescript"] == "7.0.2"
    assert pkg["devDependencies"]["@types/node"] == "22.20.5"

    starter_pkg = starter_dir / "package.json"
    assert starter_pkg.is_symlink()
    assert not starter_pkg.readlink().is_absolute()
    assert starter_pkg.resolve() == (kit_dir / "package.json").resolve()
    for config_name in ("biome.json", "playwright.config.ts", "tsconfig.json"):
        assert (starter_dir / config_name).read_bytes() == (kit_dir / config_name).read_bytes()


def test_apply_kit_delivers_a_working_playwright_project(tmp_path: Path) -> None:
    """Applying the Playwright kit normalizes name, skips docs, and passes its smoke test."""
    result = run_apply_kit("playwright", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    pkg = json.loads((tmp_path / "package.json").read_text())
    assert pkg["name"] == "playwright-config-kit-project"
    assert (tmp_path / "biome.json").is_file()
    assert (tmp_path / "playwright.config.ts").is_file()
    assert (tmp_path / "tsconfig.json").is_file()

    if (REPO_ROOT / "starters/playwright/node_modules").is_dir():
        assert "Smoke test Playwright: biome check" in result.stdout
        assert "Smoke test Playwright: tsc --noEmit" in result.stdout
        if "omitido (falta binario Chromium)" not in result.stdout:
            assert "Smoke test Playwright: playwright test" in result.stdout


def test_check_versions_rejects_non_exact_playwright_pin(
    tmp_path: Path, version_root: Path
) -> None:
    """A caret range in playwright/package.json fails the exact-pin check."""
    pw_kit = version_root / "templates/playwright"
    pw_starter = version_root / "starters/playwright"
    pw_kit.mkdir()
    pw_starter.mkdir()
    (pw_kit / "package.json").write_text(
        json.dumps(
            {
                "name": "starter-playwright",
                "packageManager": "pnpm@12.18.0",
                "devDependencies": {
                    "@biomejs/biome": "2.6.8",
                    "@playwright/test": "^1.65.1",
                    "typescript": "7.0.2",
                },
            }
        )
    )
    (pw_starter / "package.json").symlink_to("../../templates/playwright/package.json")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "playwright",
            "config_dir": "templates/playwright",
            "starter_dir": "starters/playwright",
            "pins": {"file": "package.json", "format": "npm-exact", "registry": "npm"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    registry = write_registry(
        tmp_path,
        pnpm="12.18.0",
        typescript="7.0.2",
        **{"@biomejs/biome": "2.6.8", "@playwright/test": "1.65.1"},
    )
    result = run_check_versions(registry, root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO playwright/@playwright/test: ^1.65.1" in result.stdout


def test_puppeteer_kit_pins_core_tools_exactly() -> None:
    """The Puppeteer config kit pins core tools exactly and shares config with its starter."""
    kit_dir = TEMPLATES / "puppeteer"
    starter_dir = REPO_ROOT / "starters" / "puppeteer"

    pkg = json.loads((kit_dir / "package.json").read_text())
    assert pkg["packageManager"] == "pnpm@12.18.0"
    assert pkg["dependencies"]["puppeteer"] == "25.17.0"
    assert pkg["devDependencies"]["@biomejs/biome"] == "2.6.8"
    assert pkg["devDependencies"]["typescript"] == "7.0.2"
    assert pkg["devDependencies"]["tsx"] == "4.23.15"
    assert pkg["devDependencies"]["@types/node"] == "22.20.5"

    starter_pkg = starter_dir / "package.json"
    assert starter_pkg.is_symlink()
    assert not starter_pkg.readlink().is_absolute()
    assert starter_pkg.resolve() == (kit_dir / "package.json").resolve()
    for config_name in ("biome.json", "tsconfig.json", "tsconfig.build.json"):
        assert (starter_dir / config_name).read_bytes() == (kit_dir / config_name).read_bytes()


def test_apply_kit_delivers_a_working_puppeteer_project(tmp_path: Path) -> None:
    """Applying the Puppeteer kit normalizes name, skips docs, and passes its smoke test."""
    result = run_apply_kit("puppeteer", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    pkg = json.loads((tmp_path / "package.json").read_text())
    assert pkg["name"] == "puppeteer-config-kit-project"
    assert (tmp_path / "biome.json").is_file()
    assert (tmp_path / "tsconfig.json").is_file()
    assert (tmp_path / "tsconfig.build.json").is_file()

    if (REPO_ROOT / "starters/puppeteer/node_modules").is_dir():
        assert "Smoke test Puppeteer: biome check" in result.stdout
        assert "Smoke test Puppeteer: tsc --noEmit" in result.stdout
        assert "Smoke test Puppeteer: tsx --test" in result.stdout
        assert "Smoke test Puppeteer: build" in result.stdout
        if "omitido (falta binario Chrome)" not in result.stdout:
            assert "Smoke test Puppeteer: node dist/main.js" in result.stdout
            assert "Automatización lista" in result.stdout


def test_check_versions_rejects_non_exact_puppeteer_pin(tmp_path: Path, version_root: Path) -> None:
    """A caret range in puppeteer/package.json fails the exact-pin check."""
    pup_kit = version_root / "templates/puppeteer"
    pup_starter = version_root / "starters/puppeteer"
    pup_kit.mkdir()
    pup_starter.mkdir()
    (pup_kit / "package.json").write_text(
        json.dumps(
            {
                "name": "starter-puppeteer",
                "packageManager": "pnpm@12.18.0",
                "dependencies": {"puppeteer": "~25.17.0"},
                "devDependencies": {"@biomejs/biome": "2.6.8", "typescript": "7.0.2"},
            }
        )
    )
    (pup_starter / "package.json").symlink_to("../../templates/puppeteer/package.json")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "puppeteer",
            "config_dir": "templates/puppeteer",
            "starter_dir": "starters/puppeteer",
            "pins": {"file": "package.json", "format": "npm-exact", "registry": "npm"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    registry = write_registry(
        tmp_path,
        pnpm="12.18.0",
        puppeteer="25.17.0",
        typescript="7.0.2",
        **{"@biomejs/biome": "2.6.8"},
    )
    result = run_check_versions(registry, root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO puppeteer/puppeteer: ~25.17.0" in result.stdout


def test_lua_kit_pins_core_tools_exactly_and_links_starter() -> None:
    """The Lua config kit pins busted/stylua exactly and shares config with its starter."""
    kit_dir = TEMPLATES / "lua"
    starter_dir = REPO_ROOT / "starters" / "lua"

    rocks = (kit_dir / "rocks.txt").read_text()
    assert "busted==2.3.0" in rocks
    assert "stylua==2.6.0" in rocks

    luarc = json.loads((kit_dir / ".luarc.json").read_text())
    assert luarc["runtime"]["version"] == "Lua 5.4"
    stylua = tomllib.loads((kit_dir / ".stylua.toml").read_text())
    assert stylua["syntax"] == "Lua54"

    starter_rocks = starter_dir / "rocks.txt"
    assert starter_rocks.is_symlink()
    assert not starter_rocks.readlink().is_absolute()
    assert starter_rocks.resolve() == (kit_dir / "rocks.txt").resolve()
    for config_name in (".luarc.json", ".stylua.toml"):
        assert (starter_dir / config_name).read_bytes() == (kit_dir / config_name).read_bytes()


def test_apply_kit_delivers_a_working_lua_project(tmp_path: Path) -> None:
    """Applying the Lua kit copies config files, skips docs, and passes its smoke test."""
    result = run_apply_kit("lua", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "README.md").exists()
    assert not (tmp_path / "EVIDENCE.md").exists()
    assert (tmp_path / "rocks.txt").is_file()
    assert (tmp_path / ".stylua.toml").is_file()
    assert (tmp_path / ".luarc.json").is_file()

    has_lua = Path("/opt/homebrew/opt/lua@5.4/bin/lua").exists() or shutil.which("lua") is not None
    has_busted = (Path.home() / ".luarocks/bin/busted").exists() or shutil.which(
        "busted"
    ) is not None
    if has_lua and shutil.which("stylua") is not None and has_busted:
        assert "Smoke test Lua: stylua --check" in result.stdout
        assert "Smoke test Lua: busted" in result.stdout
        assert "Hola, Lua" in result.stdout


def test_apply_kit_refuses_to_overwrite_existing_rocks_txt(tmp_path: Path) -> None:
    """An existing rocks.txt is left untouched when applying the Lua kit."""
    sentinel = "busted==2.0.0\n"
    (tmp_path / "rocks.txt").write_text(sentinel)

    result = run_apply_kit("lua", tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "rocks.txt").read_text() == sentinel


def test_check_versions_rejects_non_exact_lua_pin(tmp_path: Path, version_root: Path) -> None:
    """A range in lua/rocks.txt fails the exact-pin check."""
    lua_kit = version_root / "templates/lua"
    lua_starter = version_root / "starters/lua"
    lua_kit.mkdir()
    lua_starter.mkdir()
    (lua_kit / "rocks.txt").write_text("busted>=2.3.0\nstylua==2.6.0\n")
    (lua_starter / "rocks.txt").symlink_to("../../templates/lua/rocks.txt")

    catalog_path = version_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["templates"].append(
        {
            "id": "lua",
            "config_dir": "templates/lua",
            "starter_dir": "starters/lua",
            "pins": {"file": "rocks.txt", "format": "luarocks-exact", "registry": "luarocks"},
        }
    )
    catalog_path.write_text(json.dumps(catalog))

    registry = write_registry(tmp_path, busted="2.3.0", stylua="2.6.0")
    result = run_check_versions(registry, root=version_root)

    assert result.returncode == 1
    assert "PIN NO EXACTO lua/busted>=2.3.0" in result.stdout


def test_documented_kit_entrypoints_are_executable() -> None:
    import os

    if os.name == "nt":
        return
    for script in (APPLY_KIT, CHECK_VERSIONS):
        assert os.access(script, os.X_OK), script
