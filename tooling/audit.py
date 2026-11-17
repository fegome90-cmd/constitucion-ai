#!/usr/bin/env python3
"""Auditoría reproducible del kit sin instalar dependencias ni descargar binarios."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED = {"python", "typescript", "java", "react", "css", "rust", "go", "lua", "playwright", "puppeteer"}
REQUIRED_OPERATIONS = {"setup", "format", "lint", "typecheck", "test", "build", "dev", "check"}
NODE = {"typescript", "react", "css", "playwright", "puppeteer"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    templates = root / "templates"
    results: list[dict] = []

    def record(template: str, check: str, status: str, detail: str = "") -> None:
        results.append({"template": template, "check": check, "status": status, "detail": detail[:1200]})

    found = {path.name for path in templates.iterdir() if path.is_dir()}
    record("catalog", "templates_expected", "PASS" if found == EXPECTED else "FAIL", f"found={sorted(found)}")
    try:
        catalog = json.loads((root / "catalog.json").read_text())
        indexed = {item["id"] for item in catalog["templates"]}
        paths_ok = all((root / item["path"] / "starter.json").is_file() for item in catalog["templates"])
        record("catalog", "catalog_json", "PASS" if indexed == EXPECTED and paths_ok else "FAIL", f"entries={len(catalog['templates'])} paths_ok={paths_ok}")
    except Exception as exc:
        record("catalog", "catalog_json", "FAIL", str(exc))

    for name in sorted(found):
        path = templates / name
        required = {"README.md", "AGENTS.md", "starter.json", ".gitignore", ".editorconfig"}
        missing = sorted(key for key in required if not (path / key).is_file())
        record(name, "base_structure", "PASS" if not missing else "FAIL", f"missing={missing}")
        try:
            manifest = json.loads((path / "starter.json").read_text())
            valid = manifest["id"] == name and set(manifest["commands"]) == REQUIRED_OPERATIONS
            record(name, "command_contract", "PASS" if valid else "FAIL", str(manifest.get("commands")))
        except Exception as error:
            record(name, "command_contract", "FAIL", str(error))
        for extension, load in [("*.json", json.loads), ("*.toml", tomllib.loads)]:
            files = list(path.rglob(extension))
            errors = []
            for file in files:
                try:
                    load(file.read_text())
                except Exception as exc:
                    errors.append(f"{file.relative_to(path)}: {exc}")
            record(name, f"syntax_{extension}", "PASS" if not errors else "FAIL", "; ".join(errors) or f"{len(files)} archivos")

        if name in NODE:
            try:
                package = json.loads((path / "package.json").read_text())
                valid = package["name"].startswith("starter-") and package["packageManager"].startswith("pnpm@")
                record(name, "package_descriptor", "PASS" if valid else "FAIL", f"node={package.get('engines')}, scripts={sorted(package.get('scripts', {}))}")
                if name in {"typescript", "react", "playwright", "puppeteer"}:
                    node_type = package.get("devDependencies", {}).get("@types/node", "")
                    record(name, "node_type_alignment", "PASS" if node_type.startswith("22.") else "FAIL", f"@types/node={node_type}; baseline node >=22.12")
                record(name, "lockfile", "WARN" if not (path / "pnpm-lock.yaml").exists() else "PASS", "Sin pnpm-lock.yaml: instalación transitiva no certificada")
            except Exception as exc:
                record(name, "package_descriptor", "FAIL", str(exc))
        if name == "python":
            record(name, "lockfile", "WARN" if not (path / "uv.lock").exists() else "PASS", "Sin uv.lock: instalación transitiva no certificada")
        if name == "java":
            try:
                ET.parse(path / "pom.xml")
                record(name, "pom_xml", "PASS")
            except Exception as exc:
                record(name, "pom_xml", "FAIL", str(exc))
            record(name, "maven_wrapper", "WARN", "Maven Wrapper pendiente de generar con Maven conectado")

    def run(name: str, check: str, command: list[str], *, cwd: Path, timeout: int = 55, env: dict | None = None) -> None:
        if not shutil.which(command[0]):
            record(name, check, "SKIP", f"{command[0]} no instalado")
            return
        try:
            out = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            record(name, check, "FAIL", str(exc))
            return
        record(name, check, "PASS" if out.returncode == 0 else "FAIL", (out.stdout + '\n' + out.stderr)[-1200:])

    py = templates / 'python'
    run('python', 'compile', [sys.executable, '-m', 'compileall', '-q', 'src', 'tests'], cwd=py)
    if importlib.util.find_spec('pytest') is not None:
        run('python', 'pytest', [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'], cwd=py)
    else:
        record('python', 'pytest', 'SKIP', 'pytest no importable en este interprete')
    for tool in ('ruff', 'pyrefly'):
        record('python', tool, 'SKIP' if not shutil.which(tool) else 'WARN', f"{tool} requiere validación en entorno con dependencias instaladas")

    go = templates / 'go'
    env = os.environ | {'GOPROXY': 'off', 'GOWORK': 'off', 'GOTOOLCHAIN': 'local'}
    run('go', 'go_test', ['go', 'test', './...'], cwd=go, env=env)
    run('go', 'go_vet', ['go', 'vet', './...'], cwd=go, env=env)
    run('go', 'go_build', ['go', 'build', './...'], cwd=go, env=env)

    java = templates / 'java'
    if shutil.which('javac'):
        with tempfile.TemporaryDirectory() as temp:
            src = java / 'src/main/java/org/example/starter/App.java'
            run('java', 'javac', ['javac', '-d', temp, str(src)], cwd=java)
            cls = Path(temp) / 'org/example/starter/App.class'
            if cls.exists():
                run('java', 'java_main', ['java', '-cp', temp, 'org.example.starter.App'], cwd=java)
    else:
        record('java', 'javac', 'SKIP', 'JDK no instalado')
    if not shutil.which('mvn'):
        record('java', 'maven_junit_spotless', 'SKIP', 'Maven/plug-ins no disponibles; JUnit+Spotless sin certificar')

    css = templates / 'css'
    run('css', 'node_test', ['node', '--test', 'tests/styles.test.mjs'], cwd=css)
    run('css', 'js_syntax', ['node', '--check', 'tests/styles.test.mjs'], cwd=css)
    pw = templates / 'playwright'
    run('playwright', 'fixture_syntax', ['node', '--check', 'src/server.mjs'], cwd=pw)
    # Valida la respuesta HTTP local SIN descargar Playwright.
    if shutil.which('node'):
        try:
            proc = subprocess.Popen(['node', 'src/server.mjs'], cwd=pw, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            try:
                body = ''
                for _ in range(25):
                    if proc.poll() is not None: break
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:4173/', timeout=.3) as response:
                            body = response.read().decode()
                            break
                    except Exception:
                        time.sleep(.1)
                record('playwright', 'http_fixture', 'PASS' if '<h1>Prueba E2E</h1>' in body else 'FAIL', 'servidor HTML local real')
            finally:
                proc.terminate()
                try: proc.communicate(timeout=2)
                except subprocess.TimeoutExpired: proc.kill(); proc.communicate()
        except Exception as exc:
            record('playwright', 'http_fixture', 'FAIL', str(exc))
    else:
        record('playwright', 'http_fixture', 'SKIP', 'Node no instalado')

    record('typescript', 'node_dependencies', 'SKIP', 'pnpm/TypeScript/Vitest/Biome no instalados en entorno offline')
    record('react', 'node_dependencies', 'SKIP', 'pnpm/Vite/React/Vitest/Biome no instalados en entorno offline')
    record('css', 'vite_biome', 'SKIP', 'pnpm/Vite/Biome no instalados en entorno offline')
    record('playwright', 'browser_e2e', 'SKIP', 'Playwright y navegador Chromium no descargados')
    record('puppeteer', 'browser_test', 'SKIP', 'Puppeteer/Chrome no instalados')
    record('rust', 'cargo_clippy_tests', 'SKIP' if not shutil.which('cargo') else 'WARN', 'Toolchain Rust no certificada')
    record('lua', 'lua_busted_stylua', 'SKIP' if not shutil.which('lua') else 'WARN', 'Toolchain Lua no certificada')

    # No confundas 'no se pudo instalar TypeScript' con un error de sintaxis real.
    ts_present = False
    if shutil.which('node') and shutil.which('npm'):
        try:
            global_npm = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True, timeout=8)
            ts_present = global_npm.returncode == 0 and (Path(global_npm.stdout.strip()) / 'typescript/package.json').is_file()
        except (OSError, subprocess.TimeoutExpired):
            pass
    if ts_present:
        run('catalog', 'typescript_syntax_only', ['node', 'tooling/ts_syntax.mjs'], cwd=root, timeout=45)
    else:
        record('catalog', 'typescript_syntax_only', 'SKIP', 'TypeScript global no instalado')
    run('generator', 'unittest', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tooling/tests', '-v'], cwd=root, timeout=70)
    totals = {status: sum(item['status'] == status for item in results) for status in ('PASS', 'FAIL', 'WARN', 'SKIP')}
    data = {'root': root.name, 'results': results, 'totals': totals, 'status': 'FAIL' if totals['FAIL'] else 'PARTIAL' if totals['WARN'] or totals['SKIP'] else 'PASS'}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'totals': totals, 'status': data['status']}, ensure_ascii=False))
    for item in results:
        if item['status'] == 'FAIL':
            print(f"FAIL {item['template']} {item['check']} {item['detail']}")
    return 1 if totals['FAIL'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
