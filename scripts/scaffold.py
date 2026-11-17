#!/usr/bin/env python3
"""Export a standalone project from a repository starter."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
IGNORE_BUILD_OUTPUT = shutil.ignore_patterns(
    ".DS_Store",
    ".git",
    ".env",
    ".env.*",
    ".venv",
    "node_modules",
    "dist",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.egg-info",
    "playwright-report",
    "test-results",
)


def starters(root: Path) -> list[str]:
    return sorted(
        path.name
        for path in (root / "starters").iterdir()
        if not path.is_symlink() and (path / "starter.json").is_file()
    )


def make(template: str, name: str, output: Path, *, root: Path = ROOT) -> Path:
    if not VALID_SLUG.fullmatch(name):
        raise ValueError("Nombre inválido: usa letras minúsculas, números y guiones")
    if template not in starters(root):
        raise ValueError("Template no reconocido")

    src = root / "starters" / template
    kit = root / "templates" / template
    dest = output.resolve() / name
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f"Ya existe: {dest}")
    if dest.is_relative_to(src.resolve()):
        raise ValueError("El destino debe estar fuera del starter de origen")

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = IGNORE_BUILD_OUTPUT(directory, names)
        parent = Path(directory)
        for filename in set(names) - ignored:
            path = parent / filename
            if path.is_symlink() and (
                parent != src
                or path.readlink().is_absolute()
                or not (kit / filename).is_file()
                or (kit / filename).is_symlink()
                or path.resolve() != (kit / filename).resolve()
            ):
                raise ValueError(f"Enlace no permitido en el starter: {path.relative_to(src)}")
        return ignored

    # Claim the destination first. A failed export cleans up only its own directory.
    dest.mkdir(parents=True)
    try:
        shutil.copytree(src, dest, dirs_exist_ok=True, ignore=ignore)
        old_slug = f"starter-{template}"
        old_module = old_slug.replace("-", "_")
        new_module = name.replace("-", "_")
        replacements = {old_slug: name, old_module: new_module}
        pattern = re.compile("|".join(map(re.escape, replacements)))

        for path in dest.rglob("*"):
            if not path.is_file():
                continue
            try:
                original = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            changed = pattern.sub(lambda match: replacements[match[0]], original)
            if changed != original:
                path.write_text(changed, encoding="utf-8")

        if template == "python" and new_module != old_module:
            (dest / "src" / old_module).rename(dest / "src" / new_module)
    except (OSError, ValueError):
        shutil.rmtree(dest)
        raise
    return dest


def main() -> int:
    choices = starters(ROOT)
    parser = argparse.ArgumentParser(description="Genera un proyecto desde un starter")
    parser.add_argument("--list", action="store_true", help="Lista starters")
    parser.add_argument("--template", choices=choices, help="Starter de origen")
    parser.add_argument("--name", help="Nombre slug del nuevo proyecto")
    parser.add_argument("--output", type=Path, default=Path.cwd(), help="Directorio de salida")
    args = parser.parse_args()
    if args.list:
        print("\n".join(choices))
        return 0
    if not args.template or not args.name:
        parser.error("Faltan --template y --name")
    try:
        result = make(args.template, args.name, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
