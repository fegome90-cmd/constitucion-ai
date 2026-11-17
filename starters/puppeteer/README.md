# Puppeteer · TypeScript + automatización de navegador

Scripts de navegación; `node:test` solo para lógica pura. El comando `pnpm dev` sí requiere navegador Chrome compatible.

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm exec puppeteer browsers install chrome
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm dev
```

Con pnpm 12 los scripts de instalación pueden estar bloqueados. Se descarga el navegador con un comando explícito y auditable. Evita instalar `puppeteer-core` junto con `puppeteer` salvo que el contexto requiera Chrome externo.

`pnpm run check` valida la lógica y ejecuta con Chrome el programa compilado.
