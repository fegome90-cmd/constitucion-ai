"""Tests de seguridad e integridad del generador, sin dependencias externas."""

import importlib.util
import json
import os
import shutil
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
            self.assertTrue((path / "src/mi_libreria/__init__.py").is_file())
            self.assertIn("mi_libreria", (path / "tests/test_greet.py").read_text())
            self.assertIn("mi-libreria", (path / "pyproject.toml").read_text())

    def test_rust_lockfile_name_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = mod.make("rust", "nuevo-rust", Path(directory))
            self.assertIn('name = "nuevo-rust"', (path / "Cargo.lock").read_text())
            self.assertIn('name = "nuevo-rust"', (path / "Cargo.toml").read_text())

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
            command = ["go", "test", "./..."]
            env = os.environ | {"GOPROXY": "off", "GOWORK": "off", "GOTOOLCHAIN": "local"}
            good = subprocess.run(
                command, cwd=path, env=env, capture_output=True, text=True, timeout=50
            )
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            source = path / "greet/greet.go"
            source.write_text(
                source.read_text().replace('return "Hola, " + clean', 'return "Adios, " + clean')
            )
            bad = subprocess.run(
                command, cwd=path, env=env, capture_output=True, text=True, timeout=50
            )
            self.assertNotEqual(bad.returncode, 0, "La regresión debe fallar")

    def test_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mod.make("go", "demo-go", Path(directory))
            with self.assertRaises(FileExistsError):
                mod.make("go", "demo-go", Path(directory))


if __name__ == "__main__":
    unittest.main()
