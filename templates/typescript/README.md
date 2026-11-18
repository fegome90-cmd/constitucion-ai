# Config kit: TypeScript

Kit mínimo y reproducible para proyectos TypeScript en Node.js (`>=22.12`). La capa ejecutable está en `starters/typescript/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| ----------- | ------------- | --------- |
| Gestor de dependencias | pnpm | 12.18.0 |
| Formatter | Biome (`biome format`) | 2.6.8 |
| Linter | Biome (`biome check`) | 2.6.8 |
| Type-checker | TypeScript (`tsc --noEmit`) | 7.0.2 |
| Test runner | Vitest | 5.1.0 |
| Ejecución / Build | tsx / TypeScript (`tsc -p tsconfig.build.json`) | 4.23.15 / 7.0.2 |

## Excluidos deliberadamente

- **ESLint y Prettier**: reemplazados por Biome para cubrir formato y lint sin configuración duplicada.
- **Jest y ts-node**: reemplazados por Vitest y `tsx` por soporte nativo de ESM y TypeScript moderno.
- **Frameworks web o de navegador**: quedan fuera del núcleo TypeScript de Node.

## Uso

```bash
scripts/apply-kit.sh typescript <destino>
```

La evidencia de adopción y compatibilidad está en `EVIDENCE.md`.
