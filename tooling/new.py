#!/usr/bin/env python3
"""Generador seguro, offline y sin dependencias externas."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
VALID_SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def make(template: str, name: str, output: Path) -> Path:
    if not VALID_SLUG.fullmatch(name):
        raise ValueError("Nombre inválido: usa letras minúsculas, números y guiones")
    src = TEMPLATES / template
    if not src.is_dir() or not (src / "starter.json").exists():
        raise ValueError("Template no reconocido")
    dest = output.resolve() / name
    if dest.exists():
        raise FileExistsError(f"Ya existe: {dest}")
    shutil.copytree(src, dest)
    old_slug = f"starter-{template}"
    old_mod = old_slug.replace("-", "_")
    new_mod = name.replace("-", "_")
    replacements = {
        old_slug: name,
        old_mod: new_mod,
        f"example.com/{old_slug}": f"example.com/{name}",
    }
    # Cambia rutas antes que contenido, y reemplaza primero las cadenas largas.
    for path in sorted(dest.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if not path.is_file():
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        changed = original
        for key, value in sorted(replacements.items(), key=lambda it: len(it[0]), reverse=True):
            changed = changed.replace(key, value)
        if path.name == "starter.json":
            # El contrato sigue identificado por template; no renombramos el campo id.
            data = json.loads(changed)
            data["id"] = template
            # Los comandos de Python deben usar el módulo nuevo.
            changed = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if changed != original:
            path.write_text(changed, encoding="utf-8")
    py = dest / "src" / old_mod
    if template == "python" and py.exists():
        py.rename(dest / "src" / new_mod)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un proyecto desde un template")
    parser.add_argument("--list", action="store_true", help="Lista templates")
    parser.add_argument("--template", choices=sorted(p.name for p in TEMPLATES.iterdir() if p.is_dir()))
    parser.add_argument("--name", help="Nombre slug del nuevo proyecto")
    parser.add_argument("--output", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.list:
        print("\n".join(sorted(p.name for p in TEMPLATES.iterdir() if p.is_dir())))
        return 0
    if not args.template or not args.name:
        parser.error("Faltan --template y --name")
    try:
        result = make(args.template, args.name, args.output)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
