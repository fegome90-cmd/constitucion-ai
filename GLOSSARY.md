# Constitución AI — Config Kits

Contexto de gobernanza agéntica del repositorio, extendido con los config kits de lenguajes que se construyen dentro de él.

## Language

**Config kit**:
Conjunto versionado de archivos de configuración para un lenguaje o toolchain, ubicado en `templates/<lenguaje>/` (o `templates/_common/` para herramientas transversales).
_Avoid_: template, scaffold, preset, starter, baseline

**Template**:
Plantilla markdown de salida usada por la skill `agentic-constitution-anchor` (`generate-template.md`, `review-template.md`).
_Avoid_: config kit, plantilla de configuración

**Version source**:
Fuente autoritativa que resuelve el número de versión de una herramienta: el registry del ecosistema (PyPI, npm, crates.io) o GitHub Releases. Context7 no es una version source: es un recuperador de documentación.
_Avoid_: oráculo de versiones, version lookup, registry de documentación

**Evidence bar**:
Umbral explícito y verificable que una herramienta debe pasar para entrar a un config kit: adopción medible, actividad reciente y documentación accesible.
_Avoid_: criterio, filtro, gate de calidad

**Starter**:
Proyecto ejecutable de ejemplo para un lenguaje, ubicado en `starters/<lenguaje>/`. Consume los pins del config kit y existe para servir de fixture a los gates, no para definir la configuración.
_Avoid_: config kit, plantilla, ejemplo

**Command contract**:
Conjunto de gates declarados en `starter.json` y reexportados por `catalog.json`: `setup`, `format`, `lint`, `typecheck`, `test`, `build`, `dev` y `check`. Un `null` significa que el gate no aplica, no que se haya ejecutado.
_Avoid_: script, tarea, pipeline

**Readiness report**:
Informe que distingue gates ejecutados (PASS/FAIL) de gates no ejecutados (SKIP) y de advertencias (WARN). Un SKIP nunca se promueve a PASS.
_Avoid_: auditoría verde, certificación, resultado final
