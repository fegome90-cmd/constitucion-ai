# Config kit: CSS

Kit mínimo y reproducible para proyectos HTML + CSS nativo con `@layer`, custom properties y Node.js (`>=22.12`). La capa ejecutable está en `starters/css/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias | pnpm | 12.18.0 |
| Formatter | Biome (`biome format`) | 2.6.8 |
| Linter | Biome (`biome check`) | 2.6.8 |
| Type-checker | — (`null` en catálogo) | — |
| Test runner | `node --test` | Node.js >=22.12 |
| Bundler / Build | Vite | 8.3.8 |

## Excluidos deliberadamente

- **Tailwind CSS / Sass / plugins PostCSS**: quedan fuera para mantener CSS estándar validado directamente por Biome y Vite.
- **Stylelint**: reemplazado por Biome CSS para evitar dos linters y configuración duplicada.
- **Playwright / regresión visual**: cubiertos por los kits dedicados `playwright` y `puppeteer`.

## Uso

Aplicar el kit a un directorio sin `package.json` ni `biome.json` previos con el script del repo:

```bash
scripts/apply-kit.sh css <destino>
```

El script normaliza `"name": "starter-css"` a `"name": "css-config-kit-project"`, omite `README.md` y `EVIDENCE.md`, y corre el smoke test (`biome check`, `node --test`, `vite build`). Para combinarlo con herramientas transversales, sigue el [procedimiento de composición manual](../_common/README.md#uso): ambos kits aportan `package.json`.

Los detalles de adopción están en `EVIDENCE.md`.
