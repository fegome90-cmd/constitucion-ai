# Config kit: _common

Herramientas transversales que no pertenecen a ningún lenguaje. Se aplica junto con el kit del lenguaje correspondiente para no ensuciar el mínimo de cada uno.

## Herramientas

| Herramienta | Versión | Fuente |
| ------------- | --------- | -------- |
| markdownlint-cli2 | 0.24.1 | npm registry |
| yamllint | 1.38.0 | PyPI |
| shellcheck-py | 0.11.0.1 | PyPI |
| codespell | 2.4.3 | PyPI |

La evidencia de adopción y mantenimiento está en `EVIDENCE.md`.

## Uso

```bash
scripts/apply-kit.sh python <destino>
scripts/apply-kit.sh _common <destino>
```
