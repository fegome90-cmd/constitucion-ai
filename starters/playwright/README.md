# Playwright E2E · Chromium + TypeScript

Test E2E real con servidor HTTP local Node (`fixtures/index.html`). Sin dependencias remotas en tiempo de prueba, excepto el navegador que debe instalarse una vez.

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm exec playwright install chromium
pnpm lint
pnpm typecheck
pnpm test
```

`webServer` inicia automáticamente el servidor de fixture. Firefox/WebKit son perfiles posteriores. No confundir `playwright` con `puppeteer`: el primero trae assertions, runner, trazas y fixtures.

Control integrado: `pnpm run check`.
