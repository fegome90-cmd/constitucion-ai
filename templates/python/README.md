# Config kit: Python

Kit mínimo y reproducible para un proyecto Python (`>=3.12`). Las versiones son exactas y fueron resueltas desde PyPI el 17 de noviembre de 2026. La capa ejecutable está en `starters/python/` y el contrato de comandos en `catalog.json` (ADR-0004).

## Categorías incluidas

| Categoría | Herramienta | Versión |
| ----------- | ------------- | --------- |
| Gestor de dependencias | uv | 0.13.9 |
| Build backend | hatchling | 1.33.0 |
| Formatter | ruff format | 0.17.5 |
| Linter | ruff check | 0.17.5 |
| Type-checker | mypy | 2.4.1 |
| Test runner | pytest | 9.2.0 |

Ruff cubre dos categorías con la misma herramienta; es una decisión deliberada para mantener el kit chico.

## Excluidos deliberadamente

- **pyrefly**: segundo type-checker. Se eligió mypy por ser la opción consolidada en este repo. Pyrefly queda como alternativa si se decide reemplazar, nunca sumar dos herramientas para la misma categoría.
- **bandit**: security-linter. Queda fuera de la configuración base para no romper el mínimo de cinco categorías. Se puede agregar como extra opcional.

## Uso

Aplicar el kit a un directorio sin `pyproject.toml` previo con el script del repo:

```bash
scripts/apply-kit.sh python <destino>
```

El script conserva los pins y la configuración de herramientas, omite `[build-system]` y `readme` del starter, y corre el smoke test. Para combinarlo con las herramientas transversales, aplicar también el kit `_common`.

La evidencia que justifica cada herramienta está en `EVIDENCE.md`.
