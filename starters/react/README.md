# React · Vite + TypeScript + Biome + Vitest

React 19, Vite 8, TS strict y Testing Library. No Tailwind, router ni biblioteca UI por defecto.

```sh
pnpm install
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm dev
```

Genera y versiona `pnpm-lock.yaml` tras la primera instalación. Las pruebas DOM requieren `jsdom`; E2E queda para el template Playwright separado.

Control integrado: `pnpm run check`.
