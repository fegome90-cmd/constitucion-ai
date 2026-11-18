# React · Vite + TypeScript + Biome + Vitest

React 19, Vite 8, TS strict y Testing Library. No Tailwind, router ni biblioteca UI por defecto.

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm format
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm dev
```

El starter ya incluye `pnpm-lock.yaml` versionado; en CI usa siempre `pnpm install --frozen-lockfile --ignore-scripts` (y `pnpm preview` para inspeccionar `dist/`). Las pruebas DOM requieren `jsdom`; E2E queda para el starter Playwright separado.

Control integrado: `pnpm run check`.
