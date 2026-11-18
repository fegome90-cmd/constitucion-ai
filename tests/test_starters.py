"""Regression tests for the public starter tooling."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scaffold_exports_self_contained_python_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "python",
            "--name",
            "review-demo",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "review-demo"
    assert (project / "src/review_demo/__init__.py").is_file()
    assert (project / "uv.lock").is_file()
    assert not (project / "pyproject.toml").is_symlink()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "python"
    assert manifest["commands"]["dev"] == "uv run python -m review_demo"
    assert not (project / ".venv").exists()


def test_readiness_report_reads_the_two_layers(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "tooling/audit.py"), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text())
    checks = {(row["template"], row["check"]): row["status"] for row in report["results"]}
    assert report["status"] == "PARTIAL"
    assert checks["catalog", "catalog_json"] == "PASS"
    assert checks["python", "lockfile"] == "PASS"
    assert checks["typescript", "lockfile"] == "PASS"
    assert checks["typescript", "config_sync"] == "PASS"
    assert checks["react", "config_sync"] == "PASS"
    assert checks["lua", "pin_source"] == "PASS"
    assert checks["playwright", "check"] == "SKIP"


def test_scaffold_exports_self_contained_react_and_typescript_starters(tmp_path: Path) -> None:
    react_res = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "react",
            "--name",
            "mi-app-react",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert react_res.returncode == 0, react_res.stderr
    react_proj = tmp_path / "mi-app-react"
    assert json.loads((react_proj / "package.json").read_text())["name"] == "mi-app-react"
    assert not (react_proj / "package.json").is_symlink()
    assert (react_proj / "pnpm-lock.yaml").is_file()
    assert "<title>mi-app-react</title>" in (react_proj / "index.html").read_text()
    assert not (react_proj / "node_modules").exists()
    assert not (react_proj / "dist").exists()

    ts_res = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "typescript",
            "--name",
            "mi-lib-ts",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ts_res.returncode == 0, ts_res.stderr
    ts_proj = tmp_path / "mi-lib-ts"
    assert json.loads((ts_proj / "package.json").read_text())["name"] == "mi-lib-ts"
    assert not (ts_proj / "package.json").is_symlink()
    assert (ts_proj / "pnpm-lock.yaml").is_file()
    assert not (ts_proj / "node_modules").exists()
    assert not (ts_proj / "dist").exists()


def test_recorded_puppeteer_check_exercises_chrome() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row
        for row in report["results"]
        if (row["template"], row["check"]) == ("puppeteer", "check")
    )

    assert check["exit_code"] == 0
    assert "Automatización lista" in check["detail"]
