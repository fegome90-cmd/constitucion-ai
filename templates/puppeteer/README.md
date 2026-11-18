# Config kit: Puppeteer (perfil)

Kit mínimo y reproducible para automatización con Chrome real, TypeScript estricto y ejecución directa vía `tsx` (`Node.js >=22.12`). La capa ejecutable está en `starters/puppeteer/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias | pnpm | 12.18.0 |
| Formatter | Biome (`biome format`) | 2.6.8 |
| Linter | Biome (`biome check`) | 2.6.8 |
| Type-checker | TypeScript (`tsc --noEmit`) | 7.0.2 |
| Test runner | `tsx --test` (`node:test`) | 4.23.15 |
| Automatización / Navegador | Puppeteer + Chrome | 25.17.0 |
| Build | `tsc -p tsconfig.build.json` | 7.0.2 |

## Excluidos deliberadamente

- **`puppeteer-core` junto con `puppeteer`**: se evita duplicar clientes salvo que el proyecto requiera conectar exclusivamente a un Chrome externo.
- **ESLint y Prettier**: reemplazados por Biome para formato y lint en una sola herramienta.
- **Runner E2E completo (assertions web y trazas)**: cubierto por el perfil separado `playwright`.

## Uso

Aplicar el kit a un directorio sin `package.json`, `biome.json`, `tsconfig.json` ni `tsconfig.build.json` previos con el script del repo:

```bash
scripts/apply-kit.sh puppeteer <destino>
```

El script normaliza `"name": "starter-puppeteer"` a `"name": "puppeteer-config-kit-project"`, omite `README.md` y `EVIDENCE.md`, y ejecuta el smoke test (`biome check`, `tsc --noEmit`, `tsx --test`, build y ejecución con Chrome si está disponible). Para combinarlo con herramientas transversales, aplicar también `_common`.

Los detalles de adopción están en `EVIDENCE.md`.
