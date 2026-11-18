# Config kit: React

Kit mínimo y reproducible para aplicaciones React 19 con Vite y TypeScript estricto. La capa ejecutable está en `starters/react/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| ----------- | ------------- | --------- |
| Gestor de dependencias | pnpm | 12.18.0 |
| Formatter | Biome (`biome format`) | 2.6.8 |
| Linter | Biome (`biome check`) | 2.6.8 |
| Type-checker | TypeScript (`tsc --noEmit`) | 7.0.2 |
| Test runner | Vitest + Testing Library + jsdom | 5.1.0 / 16.3.0 / 27.0.0 |
| Bundler / Runtime | Vite + React (`react`, `react-dom`) | 8.3.8 / 19.3.1 |

## Excluidos deliberadamente

- **Tailwind CSS / Sass / librerías UI**: quedan fuera del núcleo mínimo; el kit usa CSS estándar validado por Biome.
- **Router y state managers externos**: se agregan por proyecto según necesidad.
- **ESLint y Prettier**: reemplazados por Biome para cubrir formato y lint en una sola herramienta.
- **E2E (Playwright/Puppeteer)**: cubiertos por los kits dedicados `playwright` y `puppeteer`.

## Uso

```bash
scripts/apply-kit.sh react <destino>
```

La evidencia de adopción y compatibilidad está en `EVIDENCE.md`.
