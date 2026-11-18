# TypeScript Node · pnpm + TS strict + Biome + Vitest

Requiere Node >=22.12, pnpm 12.

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm format
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm dev
pnpm start
```

El starter ya incluye `pnpm-lock.yaml` versionado; en CI usa siempre `pnpm install --frozen-lockfile --ignore-scripts`. No agregar ESLint/Prettier junto a Biome salvo necesidad justificada.

Control integrado: `pnpm run check`.
