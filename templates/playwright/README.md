# Config kit: Playwright (perfil)

Kit mínimo y reproducible para pruebas E2E con Chromium real, servidor HTTP local y TypeScript estricto (`Node.js >=22.12`). La capa ejecutable está en `starters/playwright/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias | pnpm | 12.18.0 |
| Formatter | Biome (`biome format`) | 2.6.8 |
| Linter | Biome (`biome check`) | 2.6.8 |
| Type-checker | TypeScript (`tsc --noEmit`) | 7.0.2 |
| Test runner / E2E | `@playwright/test` + Chromium | 1.65.1 |
| Build | — (`null` en catálogo) | — |

## Excluidos deliberadamente

- **Firefox y WebKit por defecto**: quedan como perfiles posteriores para mantener acotada la descarga de binarios en `setup`.
- **ESLint y Prettier**: reemplazados por Biome para formato y lint en una sola herramienta.
- **Automatización sin runner E2E**: cubierta por el perfil separado `puppeteer`.

## Uso

Aplicar el kit a un directorio sin `package.json`, `biome.json`, `playwright.config.ts` ni `tsconfig.json` previos con el script del repo:

```bash
scripts/apply-kit.sh playwright <destino>
```

El script normaliza `"name": "starter-playwright"` a `"name": "playwright-config-kit-project"`, omite `README.md` y `EVIDENCE.md`, y ejecuta el smoke test (`biome check`, `tsc --noEmit` y `playwright test` cuando Chromium está disponible). Para combinarlo con herramientas transversales, sigue el [procedimiento de composición manual](../_common/README.md#uso): ambos kits aportan `package.json`.

Los detalles de adopción están en `EVIDENCE.md`.
