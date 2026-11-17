#!/usr/bin/env python3
"""Audit the two-layer catalog and optionally execute its starter gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess  # nosec B404 - Required for the opt-in starter gates.
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXPECTED = {
    "css",
    "go",
    "java",
    "lua",
    "playwright",
    "puppeteer",
    "python",
    "react",
    "rust",
    "typescript",
}
REQUIRED_OPERATIONS = {"setup", "format", "lint", "typecheck", "test", "build", "dev", "check"}
STARTER_FILES = {"README.md", "AGENTS.md", "starter.json", ".gitignore", ".editorconfig"}
LOCKFILES = dict.fromkeys(
    {"css", "typescript", "react", "playwright", "puppeteer"}, "pnpm-lock.yaml"
) | {
    "python": "uv.lock",
    "rust": "Cargo.lock",
}


def load_catalog(root: Path) -> list[dict[str, Any]]:
    catalog = json.loads((root / "catalog.json").read_text())
    entries: list[dict[str, Any]] = catalog["templates"]
    names = {entry["id"] for entry in entries}
    if catalog["schema_version"] != 2 or len(entries) != len(EXPECTED) or names != EXPECTED:
        raise ValueError("Se esperan diez entradas únicas del catálogo v2")
    for layer, field in (("templates", "config_dir"), ("starters", "starter_dir")):
        for entry in entries:
            relative = Path(layer) / entry["id"]
            if Path(entry[field]) != relative or not (root / relative).is_dir():
                raise ValueError(f"Ruta inválida o ausente: {relative}")
    return entries


def audit_structure(root: Path, entry: dict[str, Any], results: list[dict[str, Any]]) -> bool:
    name = entry["id"]
    config = root / entry["config_dir"]
    starter = root / entry["starter_dir"]
    missing = sorted(file for file in STARTER_FILES if not (starter / file).is_file())
    results.append(
        result(name, "base_structure", "FAIL" if missing else "PASS", ", ".join(missing))
    )

    commands = entry["commands"]
    manifest = (
        json.loads((starter / "starter.json").read_text()) if "starter.json" not in missing else {}
    )
    valid = (
        manifest.get("id") == name
        and manifest.get("commands") == commands
        and set(commands) == REQUIRED_OPERATIONS
        and all(
            value is None or isinstance(value, str) and bool(value.strip())
            for value in commands.values()
        )
        and all(commands[gate] for gate in ("setup", "check"))
    )
    results.append(result(name, "command_contract", "PASS" if valid else "FAIL"))

    pin = Path(entry["pins"]["file"])
    source = config / pin
    link = starter / pin
    linked = (
        source.is_file()
        and not source.is_symlink()
        and link.is_symlink()
        and not link.readlink().is_absolute()
        and link.resolve() == source
    )
    results.append(
        result(name, "pin_source", "PASS" if linked else "FAIL", str(source.relative_to(root)))
    )

    lockfile = LOCKFILES.get(name)
    locked = lockfile is None or (starter / lockfile).is_file()
    if lockfile:
        results.append(result(name, "lockfile", "PASS" if locked else "FAIL", lockfile))
    return not missing and valid and linked and locked


def result(
    name: str, check: str, status: str, detail: str = "", **evidence: str | int
) -> dict[str, Any]:
    return {"template": name, "check": check, "status": status, "detail": detail, **evidence}


def run_gates(root: Path, entry: dict[str, Any], results: list[dict[str, Any]]) -> None:
    name = entry["id"]
    commands = entry["commands"]
    with tempfile.TemporaryDirectory(prefix="starter-audit-") as directory:
        project = Path(directory).resolve() / f"starter-{name}"
        # The caller explicitly opted in to executing a trusted checkout.
        export = subprocess.run(  # nosec B603
            [
                sys.executable,
                str(root / "scripts/scaffold.py"),
                "--template",
                name,
                "--name",
                project.name,
                "--output",
                directory,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if export.returncode != 0:
            results.append(
                result(name, "scaffold", "FAIL", export.stderr.strip(), exit_code=export.returncode)
            )
            results.extend(
                result(name, gate, "SKIP", "Falló la exportación") for gate in ("setup", "check")
            )
            return

        lockfile = project / LOCKFILES[name] if name in LOCKFILES else None
        digest = hashlib.sha256(lockfile.read_bytes()).hexdigest() if lockfile else None
        environment = os.environ | {
            "UV_FROZEN": "true",
            "GOWORK": "off",
            "GOTOOLCHAIN": "local",
            "CARGO_NET_OFFLINE": "true",
        }
        setup_passed = True
        for gate in ("setup", "check"):
            command = commands[gate]
            if not setup_passed:
                results.append(result(name, gate, "SKIP", "Setup incompleto", command=command))
                continue
            try:
                # Execute the reviewed command contract in the exported project.
                outcome = subprocess.run(  # nosec B603
                    ["/bin/sh", "-ec", command],
                    cwd=project,
                    env=environment,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=300,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append(result(name, gate, "FAIL", str(error), command=command))
                setup_passed = False
                continue
            log = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", outcome.stdout + outcome.stderr)
            log = log.replace(str(project), ".").replace(str(Path.home()), "$HOME")
            detail = log.strip()[-3000:]
            setup_passed = outcome.returncode == 0
            status = "PASS" if setup_passed else "SKIP" if outcome.returncode == 127 else "FAIL"
            results.append(
                result(
                    name,
                    gate,
                    status,
                    detail,
                    command=command,
                    exit_code=outcome.returncode,
                )
            )
        if lockfile:
            unchanged = (
                lockfile.is_file() and hashlib.sha256(lockfile.read_bytes()).hexdigest() == digest
            )
            results.append(
                result(
                    name,
                    "lock_integrity",
                    "PASS" if unchanged else "FAIL",
                    f"{lockfile.name} {digest}",
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Write the readiness report as JSON")
    parser.add_argument(
        "--run-gates", action="store_true", help="Run setup and check from a trusted checkout"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    results: list[dict[str, Any]] = []
    try:
        entries = load_catalog(root)
    except (OSError, TypeError, ValueError, KeyError) as error:
        results.append(result("catalog", "catalog_json", "FAIL", str(error)))
        entries = []
    else:
        results.append(result("catalog", "catalog_json", "PASS", f"{len(entries)} starters"))

    for entry in entries:
        name = entry["id"]
        try:
            valid = audit_structure(root, entry, results)
            if args.run_gates and valid:
                run_gates(root, entry, results)
            else:
                reason = "Ejecutar con --run-gates" if valid else "Estructura inválida"
                results.extend(result(name, gate, "SKIP", reason) for gate in ("setup", "check"))
        except (OSError, TypeError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            results.append(result(name, "audit", "FAIL", str(error)))

    counts = Counter(row["status"] for row in results)
    totals = {status: counts[status] for status in ("PASS", "FAIL", "WARN", "SKIP")}
    status = "FAIL" if counts["FAIL"] else "PARTIAL" if counts["SKIP"] or counts["WARN"] else "PASS"
    report = {
        "root": root.name,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "environment": f"{platform.system()} {platform.machine()}",
        "results": results,
        "totals": totals,
        "status": status,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"totals": totals, "status": status}, ensure_ascii=False))
    for row in results:
        if row["status"] == "FAIL":
            print(f"FAIL {row['template']} {row['check']} {row['detail']}")
    return int(status == "FAIL" or (args.run_gates and status != "PASS"))


if __name__ == "__main__":
    raise SystemExit(main())
