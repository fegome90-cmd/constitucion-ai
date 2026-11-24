# Config kit: _common

Herramientas transversales que no pertenecen a ningún lenguaje. Se combina con el kit del lenguaje correspondiente, siempre que no se sobrescriban archivos existentes.

## Herramientas

| Herramienta | Versión | Fuente |
| ------------- | --------- | -------- |
| markdownlint-cli2 | 0.24.1 | npm registry |
| yamllint | 1.38.0 | PyPI |
| shellcheck-py | 0.11.0.1 | PyPI |
| codespell | 2.4.3 | PyPI |

La evidencia de adopción y mantenimiento está en `EVIDENCE.md`.

## Diferencias con la configuración de este repo

Estos archivos se extrajeron de la configuración del repo, con cuatro divergencias deliberadas: no se copian la lista de palabras en español de `ignore-words-list`, el skip de `_ctx/` ni la excepción ortográfica de hashes SHA-512 de los lockfiles del repositorio. El kit añade `node_modules` al skip de codespell. Las demás reglas se conservan.

## Uso

```bash
scripts/apply-kit.sh python <destino>
scripts/apply-kit.sh _common <destino>
```

Esta aplicación consecutiva funciona cuando no existen nombres de archivo en conflicto. Si el kit del lenguaje ya aportó un `package.json` (por ejemplo CSS, TypeScript, React, Playwright o Puppeteer), el script rechaza la segunda aplicación antes de copiar ningún archivo. Integra manualmente la dependencia transversal fijada en `templates/_common/package.json`, conservando el `package.json` existente, y las demás configuraciones que no entren en conflicto. Reconcilia el lockfile con el gestor de dependencias del proyecto; no existe fusión automática.
