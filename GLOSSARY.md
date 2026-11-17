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
