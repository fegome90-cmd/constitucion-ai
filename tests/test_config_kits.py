"""Tests for config kits, exercised through their public seams."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES = REPO_ROOT / "templates"
APPLY_KIT = REPO_ROOT / "scripts" / "apply-kit.sh"
CHECK_VERSIONS = REPO_ROOT / "scripts" / "check-versions.sh"
MATCHING_VERSIONS = {
    "uv": "0.13.9",
    "ruff": "0.17.5",
    "mypy": "2.4.1",
    "pytest": "9.2.0",
    "yamllint": "1.38.0",
    "shellcheck-py": "0.11.0.1",
    "codespell": "2.4.3",
    "markdownlint-cli2": "0.24.1",
    "@biomejs/biome": "2.6.8",
    "@playwright/test": "1.65.1",
    "@testing-library/react": "16.3.0",
    "@types/node": "22.20.5",
    "@types/react": "19.3.0",
    "@types/react-dom": "19.3.0",
    "@vitejs/plugin-react": "6.3.0",
    "jsdom": "27.0.0",
    "puppeteer": "25.17.0",
    "react": "19.3.1",
    "react-dom": "19.3.1",
    "tsx": "4.23.15",
    "typescript": "7.0.2",
    "vite": "8.3.8",
    "vitest": "5.1.0",
    "busted": "2.3.0",
    "stylua": "2.6.0",
    "junit": "6.0.0",
    "rust": "1.100.0",
    "go": "1.23",
}


def write_registry(destination: Path, **overrides: str) -> Path:
    registry = destination / "registry.json"
    registry.write_text(json.dumps({**MATCHING_VERSIONS, **overrides}))
    return registry


def run_check_versions(registry_file: Path, root: Path | None = None) -> subprocess.CompletedProcess[str]:
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
            "setup", "format", "lint", "typecheck", "test", "build", "dev", "check"
        }


def test_apply_kit_delivers_a_working_python_project(tmp_path: Path) -> None:
    """Applying the Python kit leaves a project whose generated config passes its smoke test."""
    result = run_apply_kit("python", tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "pyproject.toml").is_file()


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


def test_check_versions_marks_an_older_exact_pin_as_advisory(tmp_path: Path) -> None:
    """An exact but older pin is reported without failing the build."""
    registry = write_registry(tmp_path, ruff="0.99.0")

    result = run_check_versions(registry)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AVISO python/ruff" in result.stdout


def test_precommit_revs_are_aligned_with_the_lockfile(tmp_path: Path) -> None:
    """The repo's pre-commit revs no longer diverge from the resolved lock versions."""
    result = run_check_versions(write_registry(tmp_path))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PRE-COMMIT DRIFT" not in result.stdout


def test_current_manifest_matches_files() -> None:
    """The final integrity manifest describes the bytes actually in the repo."""
    lines = (REPO_ROOT / "MANIFEST.current.sha256").read_text().splitlines()
    assert lines
    for line in lines:
        expected, relative = line.split("  ", 1)
        actual = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_check_versions_rejects_a_minimum_instead_of_an_exact_pin(tmp_path: Path) -> None:
    """A reverted range pin fails the verifier instead of being silently skipped."""
    root = tmp_path / "root"
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copy2(REPO_ROOT / "catalog.json", root / "catalog.json")
    pyproject = root / "templates" / "python" / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace("ruff==0.17.5", "ruff>=0.17.5"))

    result = run_check_versions(write_registry(tmp_path), root=root)

    assert result.returncode == 1
    assert "PIN NO EXACTO python/ruff>=0.17.5" in result.stdout
