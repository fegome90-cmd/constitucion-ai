# Config kit: Python

Kit mínimo y reproducible para un proyecto Python. Las versiones son exactas y fueron resueltas desde el registry el 17 de noviembre de 2026.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| ----------- | ------------- | --------- |
| Gestor de dependencias | uv | 0.13.9 |
| Formatter | ruff format | 0.17.5 |
| Linter | ruff check | 0.17.5 |
| Type-checker | mypy | 2.4.1 |
| Test runner | pytest | 9.2.0 |

Ruff cubre dos categorías con la misma herramienta; es una decisión deliberada para mantener el kit chico.

## Excluidos deliberadamente

- **pyrefly**: segundo type-checker. Se eligió mypy por ser la opción consolidada en este repo. Pyrefly queda como alternativa si se decide reemplazar, nunca sumar (ver ADR-0002 y el spec).
- **bandit**: security-linter. Queda fuera de la configuración base para no romper el mínimo de cinco categorías. Se puede agregar como extra opcional.

## Uso

Aplicar el kit con el script del repo:

```bash
scripts/apply-kit.sh python <destino>
```

El script copia los archivos y corre el smoke test. Para combinarlo con las herramientas transversales, aplicar también el kit `_common`.

La evidencia que justifica cada herramienta está en `EVIDENCE.md`.
