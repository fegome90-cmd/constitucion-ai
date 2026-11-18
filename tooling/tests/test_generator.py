"""Tests de seguridad e integridad del generador, sin dependencias externas."""

import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("starter_generator", ROOT / "scripts/scaffold.py")
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class GeneratorTests(unittest.TestCase):
    def test_generates_all_ten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for template in mod.starters(ROOT):
                path = mod.make(template, f"demo-{template}", Path(directory))
                self.assertTrue((path / "README.md").exists())
                self.assertEqual(json.loads((path / "starter.json").read_text())["id"], template)

    def test_python_module_is_renamed_and_imported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("python", "mi-libreria", Path(directory))
            self.assertFalse((path / "src/starter_python").exists())
            self.assertTrue((path / "src/mi_libreria/__init__.py").is_file())
            self.assertTrue((path / "src/mi_libreria/__main__.py").is_file())
            self.assertIn("mi_libreria", (path / "tests/test_greet.py").read_text())
            self.assertIn('name = "mi-libreria"', (path / "pyproject.toml").read_text())
            self.assertIn('name = "mi-libreria"', (path / "uv.lock").read_text())
            self.assertIn("python -m mi_libreria", (path / "starter.json").read_text())

    def test_rust_lockfile_name_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("rust", "nuevo-rust", Path(directory))
            self.assertFalse((path / "Cargo.toml").is_symlink())
            self.assertFalse((path / "rust-toolchain.toml").is_symlink())
            self.assertFalse((path / "target").exists())
            self.assertIn('name = "nuevo-rust"', (path / "Cargo.lock").read_text())
            self.assertIn('name = "nuevo-rust"', (path / "Cargo.toml").read_text())
            self.assertIn("nuevo_rust::greet", (path / "src/main.rs").read_text())

    def test_generated_rust_runs_and_detects_regression(self) -> None:
        cargo_bin = Path.home() / ".cargo" / "bin"
        if not ((cargo_bin / "cargo").exists() or shutil.which("cargo") is not None):
            self.skipTest("Rust/Cargo not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("rust", "codigo-rust", Path(directory))
            env = os.environ | {
                "PATH": f"{cargo_bin}:{os.environ['PATH']}"
                if cargo_bin.is_dir()
                else os.environ["PATH"],
                "CARGO_NET_OFFLINE": "true",
            }
            for cmd in (
                ["cargo", "fmt", "--all", "--", "--check"],
                ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                ["cargo", "test", "--locked"],
                ["cargo", "build", "--locked"],
            ):
                ok = subprocess.run(
                    cmd, cwd=path, env=env, capture_output=True, text=True, timeout=60
                )
                self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            source = path / "src/lib.rs"
            source.write_text(source.read_text().replace("Hola, {trimmed}", "Adios, {trimmed}"))
            bad = subprocess.run(
                ["cargo", "test", "--locked"],
                cwd=path,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for name in ("../escape", "demo/../../escape", "UPPER", ".hidden"):
                with self.assertRaises(ValueError):
                    mod.make("python", name, Path(directory))

    def test_generated_python_runs_and_detects_regression(self) -> None:
        if importlib.util.find_spec("pytest") is None:
            self.skipTest("pytest module not importable in this interpreter")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("python", "codigo-py", Path(directory))
            command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
            good = subprocess.run(command, cwd=path, capture_output=True, text=True, timeout=35)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            source = path / "src/codigo_py/__init__.py"
            source.write_text(
                source.read_text().replace('f"Hola, {name.strip()}"', 'f"Adios, {name.strip()}"')
            )
            bad = subprocess.run(command, cwd=path, capture_output=True, text=True, timeout=35)
            self.assertNotEqual(bad.returncode, 0, "Un cambio de salida debe romper los tests")

    def test_generated_go_runs_and_detects_regression(self) -> None:
        if shutil.which("go") is None:
            self.skipTest("Go not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("go", "codigo-go", Path(directory))
            self.assertFalse((path / "go.mod").is_symlink())
            self.assertIn("module example.com/codigo-go", (path / "go.mod").read_text())
            self.assertIn(
                '"example.com/codigo-go/greet"', (path / "cmd/starter/main.go").read_text()
            )
            env = os.environ | {"GOPROXY": "off", "GOWORK": "off", "GOTOOLCHAIN": "local"}
            for cmd in (["go", "vet", "./..."], ["go", "test", "./..."], ["go", "build", "./..."]):
                ok = subprocess.run(
                    cmd, cwd=path, env=env, capture_output=True, text=True, timeout=50
                )
                self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            source = path / "greet/greet.go"
            source.write_text(
                source.read_text().replace('return "Hola, " + clean', 'return "Adios, " + clean')
            )
            bad = subprocess.run(
                ["go", "test", "./..."],
                cwd=path,
                env=env,
                capture_output=True,
                text=True,
                timeout=50,
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_generated_java_runs_and_detects_regression(self) -> None:
        if shutil.which("mvn") is None or shutil.which("java") is None:
            self.skipTest("Java/Maven not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("java", "codigo-java", Path(directory))
            self.assertFalse((path / "pom.xml").is_symlink())
            self.assertFalse((path / "target").exists())
            self.assertIn("<artifactId>codigo-java</artifactId>", (path / "pom.xml").read_text())
            good = subprocess.run(
                ["mvn", "-q", "spotless:check", "verify"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            source = path / "src/main/java/org/example/starter/App.java"
            source.write_text(source.read_text().replace('"Hola, "', '"Adios, "'))
            bad = subprocess.run(
                ["mvn", "-q", "test"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_generated_css_runs_and_detects_regression(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("Node.js not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("css", "codigo-css", Path(directory))
            self.assertFalse((path / "package.json").is_symlink())
            self.assertFalse((path / "node_modules").exists())
            self.assertFalse((path / "dist").exists())
            self.assertEqual(json.loads((path / "package.json").read_text())["name"], "codigo-css")
            command = ["node", "--test", "tests/styles.test.mjs"]
            good = subprocess.run(command, cwd=path, capture_output=True, text=True, timeout=30)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            styles = path / "src/styles.css"
            styles.write_text(styles.read_text().replace("@layer tokens", "@layer colors"))
            bad = subprocess.run(command, cwd=path, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_generated_playwright_runs_and_detects_regression(self) -> None:
        starter_nm = ROOT / "starters/playwright/node_modules"
        if shutil.which("node") is None or not starter_nm.is_dir():
            self.skipTest("Node.js or starters/playwright/node_modules not available")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("playwright", "codigo-e2e", Path(directory))
            self.assertFalse((path / "package.json").is_symlink())
            self.assertFalse((path / "node_modules").exists())
            self.assertFalse((path / "playwright-report").exists())
            self.assertFalse((path / "test-results").exists())
            self.assertEqual(json.loads((path / "package.json").read_text())["name"], "codigo-e2e")
            (path / "node_modules").symlink_to(starter_nm)
            has_chromium = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "-e",
                    (
                        'import { chromium } from "@playwright/test"; '
                        'import { existsSync } from "node:fs"; '
                        "process.exit(existsSync(chromium.executablePath()) ? 0 : 1);"
                    ),
                ],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if has_chromium.returncode != 0:
                self.skipTest("Playwright Chromium not installed")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                port = str(sock.getsockname()[1])
            env = os.environ | {"CI": "true", "PLAYWRIGHT_HTML_OPEN": "never", "PORT": port}
            for cmd in (
                ["./node_modules/.bin/biome", "check", "."],
                ["./node_modules/.bin/tsc", "--noEmit"],
                ["./node_modules/.bin/playwright", "test"],
            ):
                ok = subprocess.run(
                    cmd, cwd=path, env=env, capture_output=True, text=True, timeout=60
                )
                self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            fixture_html = path / "fixtures/index.html"
            fixture_html.write_text(
                fixture_html.read_text().replace(
                    '<output id="count">0</output>', '<output id="count">9</output>'
                )
            )
            bad = subprocess.run(
                ["./node_modules/.bin/playwright", "test"],
                cwd=path,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_generated_puppeteer_runs_and_detects_regression(self) -> None:
        starter_nm = ROOT / "starters/puppeteer/node_modules"
        if shutil.which("node") is None or not starter_nm.is_dir():
            self.skipTest("Node.js or starters/puppeteer/node_modules not available")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("puppeteer", "codigo-puppeteer", Path(directory))
            self.assertFalse((path / "package.json").is_symlink())
            self.assertFalse((path / "node_modules").exists())
            self.assertFalse((path / "dist").exists())
            self.assertEqual(
                json.loads((path / "package.json").read_text())["name"], "codigo-puppeteer"
            )
            (path / "node_modules").symlink_to(starter_nm)
            for cmd in (
                ["./node_modules/.bin/biome", "check", "."],
                ["./node_modules/.bin/tsc", "--noEmit"],
                ["./node_modules/.bin/tsx", "--test", "tests/utils.test.ts"],
                ["./node_modules/.bin/tsc", "-p", "tsconfig.build.json"],
            ):
                ok = subprocess.run(cmd, cwd=path, capture_output=True, text=True, timeout=60)
                self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            has_chrome = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "-e",
                    (
                        'import puppeteer from "puppeteer"; '
                        'import { existsSync } from "node:fs"; '
                        "process.exit(existsSync(await puppeteer.executablePath()) ? 0 : 1);"
                    ),
                ],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if has_chrome.returncode == 0:
                run = subprocess.run(
                    ["node", "dist/main.js"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn("Automatización lista", run.stdout)
            utils = path / "src/utils.ts"
            utils.write_text(
                utils.read_text().replace("return trimmed;", "return trimmed.toUpperCase();")
            )
            bad = subprocess.run(
                ["./node_modules/.bin/tsx", "--test", "tests/utils.test.ts"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_generated_lua_runs_and_detects_regression(self) -> None:
        extra_bins = [
            str(path)
            for path in (Path("/opt/homebrew/opt/lua@5.4/bin"), Path.home() / ".luarocks/bin")
            if path.is_dir()
        ]
        path_env = ":".join([*extra_bins, os.environ["PATH"]]) if extra_bins else os.environ["PATH"]
        if any(shutil.which(tool, path=path_env) is None for tool in ("lua", "stylua", "busted")):
            self.skipTest("Lua/StyLua/busted not available")
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("lua", "codigo-lua", Path(directory))
            self.assertFalse((path / "rocks.txt").is_symlink())
            self.assertTrue((path / ".stylua.toml").is_file())
            self.assertTrue((path / ".luarc.json").is_file())
            env = os.environ | {"PATH": path_env}
            for cmd in (["stylua", "--check", "src", "spec"], ["busted"], ["lua", "src/main.lua"]):
                ok = subprocess.run(
                    cmd, cwd=path, env=env, capture_output=True, text=True, timeout=30
                )
                self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            source = path / "src/starter.lua"
            source.write_text(source.read_text().replace('"Hola, " .. clean', '"Adios, " .. clean'))
            bad = subprocess.run(
                ["busted"], cwd=path, env=env, capture_output=True, text=True, timeout=30
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mod.make("go", "demo-go", Path(directory))
            with self.assertRaises(FileExistsError):
                mod.make("go", "demo-go", Path(directory))


if __name__ == "__main__":
    unittest.main()
