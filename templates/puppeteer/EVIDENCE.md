# Evidencia de la evidence bar — kit puppeteer

Relevamiento del 17 de noviembre de 2026. Barra: ≥1M descargas semanales o ≥5k estrellas, y actividad en los últimos seis meses. Un `NO PASA` no se oculta.

| Herramienta | Versión | Adopción | Actividad | Fuente | Estado |
| --- | --- | --- | --- | --- | --- |
| Puppeteer | 25.17.0 | 15.502.027 desc/sem | release 2026-11-10 | npm registry | PASA |
| TypeScript | 7.0.2 | 433.588.805 desc/sem | commits 2026-11-17 | npm registry | PASA |
| tsx | 4.23.15 | 142.327.240 desc/sem | release 2026-09-20 | npm registry | PASA |
| Biome (`@biomejs/biome`) | 2.6.8 | 27.853.046 desc/sem | release 2026-11-15 | npm registry | PASA |
| pnpm | 12.18.0 | ≥1M desc/sem | release 2026-11 | npm registry | PASA |
| `@types/node` | 22.20.5 | ≥1M desc/sem | paquetes DefinitelyTyped activos | npm registry | PASA |

Perfil de automatización, no lenguaje base. El gate usa Chrome real (`chrome@157.0.8103.50`); los tests unitarios de utilidades usan `tsx --test` (`node:test`). `@types/node 22.20.5` se mantiene alineado con `engines.node >=22.12`. `Biome 2.6.8` se publicó el 2026-11-15 (soak < 7 días en la fecha del relevamiento; ver ADR-0003).
