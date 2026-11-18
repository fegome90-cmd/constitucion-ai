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

    assert "ruff==0.17.5" in pyproject
    assert "mypy==2.4.1" in pyproject
    assert "pytest==9.2.0" in pyproject
    assert "[tool.ruff]" in pyproject
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
    config = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert config["project"]["name"] == "python-config-kit-project"
    assert "readme" not in config["project"]
    assert "build-system" not in config


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


@pytest.mark.parametrize("kit", ["react", "typescript"])
def test_apply_kit_refuses_to_overwrite_existing_package_json(tmp_path: Path, kit: str) -> None:
    """An existing JS/TS package.json is left untouched when applying a kit."""
    sentinel = '{"name": "existing-app"}\n'
    (tmp_path / "package.json").write_text(sentinel)

    result = run_apply_kit(kit, tmp_path)

    assert result.returncode == 1
    assert (tmp_path / "package.json").read_text() == sentinel
