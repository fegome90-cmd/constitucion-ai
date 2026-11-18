# Config kits

Cada directorio de primer nivel es un config kit: un conjunto versionado de archivos de configuración para un lenguaje o toolchain. `_common` contiene las herramientas transversales. `python` fue el piloto inicial; el catálogo completo (`catalog.json`) integra los diez kits (`css`, `go`, `java`, `lua`, `playwright`, `puppeteer`, `python`, `react`, `rust`, `typescript`) junto con sus starters ejecutables en `starters/`.

## Estructura de un kit

Todo kit sigue la misma forma, sin excepciones:

- Archivos de configuración reales, con pins exactos.
- `README.md` con las categorías incluidas y las exclusiones deliberadas.
- `EVIDENCE.md` con la tabla de la evidence bar.
- Sin generadores, sin plantillas con estado, sin variables sin resolver.

Los documentos del kit no se copian al destino; `apply-kit.sh` copia solo la configuración.

## Cómo construir un kit nuevo

1. **Definir las cinco categorías.** Gestor de dependencias, formatter, linter, type-checker y test runner. Varias categorías pueden caer en la misma herramienta, pero cada categoría debe estar cubierta por una sola opción.
2. **Aplicar la evidence bar.** Para cada candidato: ≥1M descargas semanales o ≥5k estrellas, actividad de commits en los últimos seis meses y documentación accesible. "Mantenido" significa commits recientes, no fecha de release. Registrar versión, descargas, release, actividad y fuente en `EVIDENCE.md`.
3. **Resolver el número desde la fuente autoritativa.** Nunca desde documentación. Context7 se usa para la sintaxis de configuración en esa versión y como señal de docs vigentes.
4. **Escribir los archivos con pins exactos.** Fijar `==` o el equivalente del ecosistema, nunca rangos mínimos.
5. **Documentar las exclusiones.** Qué se dejó afuera y por qué, en el `README.md` del kit.
6. **Extender el smoke test.** Agregar el caso del lenguaje al seam ya existente en `apply-kit.sh`. No crear un seam nuevo.
7. **Verificar.** Correr `check-versions.sh` en vivo y confirmar que no haya drift.

## Fuentes de versión por ecosistema

| Lenguaje / perfil | Registry / fuente autoritativa |
| ---------- | ------------------------------- |
| Python | PyPI JSON API |
| TypeScript | npm registry (`/latest`) |
| React | npm registry (`/latest`) |
| CSS | npm registry (`/latest`) |
| Playwright | npm registry (`/latest`) |
| Puppeteer | npm registry (`/latest`) |
| Java | Maven Central |
| Rust | crates.io API |
| Go | proxy.golang.org / GitHub Releases |
| Lua | LuaRocks / GitHub Releases |

## Estado de integración y seams

Los diez kits del catálogo y `_common` están integrados en `templates/` y enlazados desde `starters/` (ADR-0004). La validación y operación siguen dos seams principales más los scripts de verificación:

- `scripts/apply-kit.sh <kit> <destino>` — copia la configuración del kit sin sobrescribir archivos existentes y corre el smoke test disponible.
- `scripts/check-versions.sh` — re-resuelve pins, verifica la consistencia entre `templates/` y `starters/`, y comprueba el alineamiento entre `.pre-commit-config.yaml` y `uv.lock`.
- `scripts/scaffold.py` y `tooling/audit.py` — exportan proyectos independientes desde `starters/` y auditan la estructura y los gates del contrato v2.

Ningún kit nuevo debe introducir un seam adicional de copia o verificación.
