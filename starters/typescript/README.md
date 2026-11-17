# TypeScript Node · pnpm + TS strict + Biome + Vitest

Requiere Node >=22.12, pnpm 12.

```sh
pnpm install
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm start
```

Tras la primera instalación, **versionar pnpm-lock.yaml** y usar `pnpm install --frozen-lockfile` en CI. No agregar ESLint/Prettier junto a Biome salvo necesidad justificada.

Control integrado: `pnpm run check`.
