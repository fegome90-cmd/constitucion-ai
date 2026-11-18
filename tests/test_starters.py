"""Regression tests for the public starter tooling."""

import json
import os
import shutil
import socket
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
    assert not (project / "src/starter_python").exists()
    assert (project / "src/review_demo/__init__.py").is_file()
    assert (project / "src/review_demo/__main__.py").is_file()
    assert (project / "src/review_demo/py.typed").is_file()
    assert (project / "uv.lock").is_file()
    assert not (project / "pyproject.toml").is_symlink()
    assert 'name = "review-demo"' in (project / "pyproject.toml").read_text()
    assert "from review_demo import greet" in (project / "tests/test_greet.py").read_text()
    assert 'name = "review-demo"' in (project / "uv.lock").read_text()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "python"
    assert manifest["commands"]["dev"] == "uv run python -m review_demo"
    assert not (project / ".venv").exists()

    if shutil.which("uv") is not None:
        sync = subprocess.run(
            ["uv", "sync", "--frozen"],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert sync.returncode == 0, sync.stdout + sync.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        dev = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["dev"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert dev.returncode == 0, dev.stdout + dev.stderr
        assert "Hola, Python" in dev.stdout


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
    assert checks["css", "base_structure"] == "PASS"
    assert checks["css", "command_contract"] == "PASS"
    assert checks["css", "pin_source"] == "PASS"
    assert checks["css", "lockfile"] == "PASS"
    assert checks["css", "config_sync"] == "PASS"
    assert checks["go", "base_structure"] == "PASS"
    assert checks["go", "command_contract"] == "PASS"
    assert checks["go", "pin_source"] == "PASS"
    assert checks["go", "config_sync"] == "PASS"
    assert checks["java", "base_structure"] == "PASS"
    assert checks["java", "command_contract"] == "PASS"
    assert checks["java", "pin_source"] == "PASS"
    assert checks["java", "config_sync"] == "PASS"
    assert checks["python", "base_structure"] == "PASS"
    assert checks["python", "command_contract"] == "PASS"
    assert checks["python", "pin_source"] == "PASS"
    assert checks["python", "lockfile"] == "PASS"
    assert checks["python", "config_sync"] == "PASS"
    assert checks["rust", "base_structure"] == "PASS"
    assert checks["rust", "command_contract"] == "PASS"
    assert checks["rust", "pin_source"] == "PASS"
    assert checks["rust", "lockfile"] == "PASS"
    assert checks["rust", "config_sync"] == "PASS"
    assert checks["typescript", "lockfile"] == "PASS"
    assert checks["typescript", "config_sync"] == "PASS"
    assert checks["react", "config_sync"] == "PASS"
    assert checks["lua", "base_structure"] == "PASS"
    assert checks["lua", "command_contract"] == "PASS"
    assert checks["lua", "pin_source"] == "PASS"
    assert checks["lua", "config_sync"] == "PASS"
    assert checks["lua", "check"] == "SKIP"
    assert checks["playwright", "base_structure"] == "PASS"
    assert checks["playwright", "command_contract"] == "PASS"
    assert checks["playwright", "pin_source"] == "PASS"
    assert checks["playwright", "lockfile"] == "PASS"
    assert checks["playwright", "config_sync"] == "PASS"
    assert checks["playwright", "check"] == "SKIP"
    assert checks["puppeteer", "base_structure"] == "PASS"
    assert checks["puppeteer", "command_contract"] == "PASS"
    assert checks["puppeteer", "pin_source"] == "PASS"
    assert checks["puppeteer", "lockfile"] == "PASS"
    assert checks["puppeteer", "config_sync"] == "PASS"
    assert checks["puppeteer", "check"] == "SKIP"


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


def test_scaffold_exports_self_contained_go_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "go",
            "--name",
            "mi-servicio-go",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-servicio-go"
    assert not (project / "go.mod").is_symlink()
    go_mod = (project / "go.mod").read_text()
    assert "module example.com/mi-servicio-go" in go_mod
    assert "\ngo 1.23\n" in go_mod
    assert '"example.com/mi-servicio-go/greet"' in (project / "cmd/starter/main.go").read_text()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "go"
    assert manifest["commands"]["dev"] == "go run ./cmd/starter"

    if shutil.which("go") is not None:
        env = os.environ | {"GOPROXY": "off", "GOWORK": "off", "GOTOOLCHAIN": "local"}
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        dev = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["dev"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert dev.returncode == 0, dev.stdout + dev.stderr
        assert "Hola, Go" in dev.stdout


def test_recorded_puppeteer_check_exercises_chrome() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row
        for row in report["results"]
        if (row["template"], row["check"]) == ("puppeteer", "check")
    )

    assert check["exit_code"] == 0
    assert "Checked 10 files" in check["detail"]
    assert "pass 2" in check["detail"]
    assert "Automatización lista" in check["detail"]


def test_recorded_python_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("python", "check")
    )

    assert check["exit_code"] == 0
    assert "All checks passed!" in check["detail"]
    assert "Success: no issues found" in check["detail"]
    assert "2 passed" in check["detail"]
    assert "Successfully built" in check["detail"]


def test_recorded_go_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("go", "check")
    )

    assert check["exit_code"] == 0
    assert "example.com/starter-go/greet" in check["detail"]
    assert "ok" in check["detail"]


def test_scaffold_exports_self_contained_java_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "java",
            "--name",
            "mi-app-java",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-app-java"
    assert not (project / "pom.xml").is_symlink()
    assert not (project / "target").exists()
    assert "<artifactId>mi-app-java</artifactId>" in (project / "pom.xml").read_text()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "java"
    assert manifest["commands"]["dev"] == "java -cp target/classes org.example.starter.App"

    if shutil.which("mvn") is not None and shutil.which("java") is not None:
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        dev = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["dev"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert dev.returncode == 0, dev.stdout + dev.stderr
        assert "Hola, Java" in dev.stdout


def test_recorded_java_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("java", "check")
    )

    assert check["exit_code"] == 0
    assert "spotless:3.10.3:check" in check["detail"]
    assert "Tests run: 2, Failures: 0" in check["detail"]
    assert "BUILD SUCCESS" in check["detail"]


def test_scaffold_exports_self_contained_rust_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "rust",
            "--name",
            "mi-crate-rust",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-crate-rust"
    assert not (project / "Cargo.toml").is_symlink()
    assert not (project / "rust-toolchain.toml").is_symlink()
    assert not (project / "target").exists()
    assert 'name = "mi-crate-rust"' in (project / "Cargo.toml").read_text()
    assert 'name = "mi-crate-rust"' in (project / "Cargo.lock").read_text()
    assert "mi_crate_rust::greet" in (project / "src/main.rs").read_text()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "rust"
    assert manifest["commands"]["dev"] == "cargo run --locked"

    cargo_bin = Path.home() / ".cargo" / "bin"
    has_cargo = (cargo_bin / "cargo").exists() or shutil.which("cargo") is not None
    if has_cargo:
        env = os.environ | {
            "PATH": f"{cargo_bin}:{os.environ['PATH']}"
            if cargo_bin.is_dir()
            else os.environ["PATH"],
            "CARGO_NET_OFFLINE": "true",
        }
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        dev = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["dev"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert dev.returncode == 0, dev.stdout + dev.stderr
        assert "Hola, Rust" in dev.stdout


def test_recorded_rust_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("rust", "check")
    )

    assert check["exit_code"] == 0
    assert "test tests::greets ... ok" in check["detail"]
    assert "1 passed; 0 failed" in check["detail"]


def test_scaffold_exports_self_contained_css_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "css",
            "--name",
            "mi-estilo-css",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-estilo-css"
    assert not (project / "package.json").is_symlink()
    assert json.loads((project / "package.json").read_text())["name"] == "mi-estilo-css"
    assert (project / "pnpm-lock.yaml").is_file()
    assert not (project / "node_modules").exists()
    assert not (project / "dist").exists()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "css"

    if shutil.which("pnpm") is not None:
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        assert (project / "dist/index.html").is_file()


def test_recorded_css_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("css", "check")
    )

    assert check["exit_code"] == 0
    assert "tokens y layers presentes" in check["detail"]
    assert "pass 1" in check["detail"]
    assert "built in" in check["detail"]


def test_scaffold_exports_self_contained_playwright_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "playwright",
            "--name",
            "mi-e2e-playwright",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-e2e-playwright"
    assert not (project / "package.json").is_symlink()
    assert json.loads((project / "package.json").read_text())["name"] == "mi-e2e-playwright"
    assert (project / "pnpm-lock.yaml").is_file()
    assert not (project / "node_modules").exists()
    assert not (project / "playwright-report").exists()
    assert not (project / "test-results").exists()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "playwright"

    if shutil.which("pnpm") is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = str(sock.getsockname()[1])
        env = os.environ | {
            "CI": "true",
            "PLAYWRIGHT_HTML_OPEN": "never",
            "PORT": port,
        }
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr


def test_recorded_playwright_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row
        for row in report["results"]
        if (row["template"], row["check"]) == ("playwright", "check")
    )

    assert check["exit_code"] == 0
    assert "Checked 10 files" in check["detail"]
    assert "tsc --noEmit" in check["detail"]
    assert "1 passed" in check["detail"]


def test_scaffold_exports_self_contained_puppeteer_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "puppeteer",
            "--name",
            "mi-bot-puppeteer",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-bot-puppeteer"
    assert not (project / "package.json").is_symlink()
    assert json.loads((project / "package.json").read_text())["name"] == "mi-bot-puppeteer"
    assert (project / "pnpm-lock.yaml").is_file()
    assert not (project / "node_modules").exists()
    assert not (project / "dist").exists()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "puppeteer"

    if shutil.which("pnpm") is not None:
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        assert "Automatización lista" in check.stdout
        assert (project / "dist/main.js").is_file()


def test_scaffold_exports_self_contained_lua_starter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/scaffold.py"),
            "--template",
            "lua",
            "--name",
            "mi-lib-lua",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    project = tmp_path / "mi-lib-lua"
    assert not (project / "rocks.txt").is_symlink()
    assert (project / ".stylua.toml").is_file()
    assert (project / ".luarc.json").is_file()
    manifest = json.loads((project / "starter.json").read_text())
    assert manifest["id"] == "lua"

    extra_bins = [
        str(path)
        for path in (Path("/opt/homebrew/opt/lua@5.4/bin"), Path.home() / ".luarocks/bin")
        if path.is_dir()
    ]
    path_env = ":".join([*extra_bins, os.environ["PATH"]]) if extra_bins else os.environ["PATH"]
    env = os.environ | {"PATH": path_env}
    has_tools = all(
        shutil.which(tool, path=path_env) is not None
        for tool in ("lua", "luarocks", "stylua", "busted")
    )
    if has_tools:
        setup = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["setup"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        check = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["check"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        dev = subprocess.run(
            ["/bin/sh", "-ec", manifest["commands"]["dev"]],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert dev.returncode == 0, dev.stdout + dev.stderr
        assert "Hola, Lua" in dev.stdout


def test_recorded_lua_check_exercises_all_gates() -> None:
    report = json.loads((ROOT / "evidencia/readiness-current.json").read_text())
    check = next(
        row for row in report["results"] if (row["template"], row["check"]) == ("lua", "check")
    )

    assert check["exit_code"] == 0
    assert "1 success / 0 failures" in check["detail"]
