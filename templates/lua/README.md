# Config kit: Lua

Kit mínimo y reproducible para proyectos Lua 5.4 con formato mediante StyLua y pruebas con `busted`. La capa ejecutable está en `starters/lua/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins de paquetes se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Runtime | Lua | 5.4.9 |
| Gestor de dependencias | LuaRocks | 3.13.0 |
| Formatter / Lint | StyLua | 2.6.0 |
| Test runner | `busted` | 2.3.0 |
| Type-checker | — (`null` en catálogo; LuaLS `.luarc.json` para editor) | — |

## Excluidos deliberadamente

- **Lua 5.5**: queda fuera hasta comprobar soporte completo de StyLua y dependencias.
- **Luacheck**: opcional por proyecto; no se incluye en el núcleo mínimo por redundancia con diagnósticos de LuaLS.
- **Lockfile forzado**: LuaRocks no impone un lockfile nativo reproducible para este starter mínimo.

## Uso

Aplicar el kit a un directorio sin `rocks.txt`, `.stylua.toml` ni `.luarc.json` previos con el script del repo:

```bash
scripts/apply-kit.sh lua <destino>
```

El script omite `README.md` y `EVIDENCE.md` y ejecuta el smoke test (`stylua --check`, `busted` y `lua src/main.lua` si el toolchain está disponible). Para combinarlo con herramientas transversales, aplicar también `_common`.

Los detalles de adopción y las excepciones están en `EVIDENCE.md`.
