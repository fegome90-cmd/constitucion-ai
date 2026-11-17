# Config kits

Cada directorio de primer nivel es un config kit: un conjunto versionado de archivos de configuración para un lenguaje o toolchain. `_common` contiene las herramientas transversales. `python` es el piloto ya construido y validado.

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

| Lenguaje | Registry / fuente autoritativa |
| ---------- | ------------------------------- |
| Python | PyPI JSON API |
| TypeScript | npm registry (`/latest`) |
| Java | Maven Central |
| React | npm registry (`/latest`) |
| CSS | npm registry (`/latest`) |
| Rust | crates.io API |
| Go | proxy.golang.org / GitHub Releases |
| Lua | LuaRocks / GitHub Releases |

## Cobertura pendiente

Los siete kits restantes no están construidos. El procedimiento de arriba es la receta; el patrón ya está validado por los dos seams:

- `scripts/apply-kit.sh <kit> <destino>` — copia la configuración y corre el smoke test.
- `scripts/check-versions.sh` — re-resuelve pins y reporta drift, incluido pre-commit contra el lockfile.

Ningún kit nuevo debe introducir un tercer seam.
