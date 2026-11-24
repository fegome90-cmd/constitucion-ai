# Python mínimo · uv + Ruff + mypy + pytest

Requisitos: Python >=3.12 y uv 0.13.9. `uv sync --frozen` crea el entorno desde el lockfile versionado.

Los pins y la configuración de herramientas viven en `templates/python/` (ADR-0004): este starter los consume, no los redefine. El type-checker es mypy; pyrefly queda documentado como alternativa descartada.

## Gates

Ejecutar los gates de `starter.json` (`check` valida formato, lint, tipos, tests y build):

```sh
uv sync --frozen
uv run ruff format .
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv build
uv run python -m starter_python
```
