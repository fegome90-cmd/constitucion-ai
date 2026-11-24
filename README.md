# Constitución de Código Agéntico

[![Version](https://img.shields.io/badge/version-v1.1-blue.svg)](./constitution/AGENTIC-CONSTITUTION.md)

> Marco fundacional para gobernanza de sistemas de IA en desarrollo de software.

## ¿Qué es esto?

Un framework de "leyes" que regula cómo los agentes de IA deben operar dentro de un sistema de desarrollo. No es un prompt engineering trick — es una **constitución operativa** que define:

- **Qué** cambios son legítimos
- **Cómo** se planifican y ejecutan
- **Quién** valida y aprueba
- **Cuándo** se requiere intervención humana

## ¿Por qué una constitución?

Los agentes de IA son poderosos pero impredecibles. Sin reglas claras:

- Cambian código sin entender el contexto
- Duplican funcionalidad que ya existe
- Ignoran convenciones del proyecto
- No dejan evidencia de sus cambios
- Expanden el alcance sin permiso

Esta constitución resuelve eso con **leyes vinculantes**, no sugerencias.

## Las 13 Leyes

| Ley | Nombre | Propósito |
|-----|--------|-----------|
| **I** | Cambio Legítimo | Toda mutación requiere intención explícita, planificación proporcional, evidencia |
| **II** | Lectura Previa | Leer antes de escribir. No duplicar. |
| **III** | Arquitectura Base | Scope, jerarquía, responsabilidades |
| **IV** | Control de Versiones | Aislamiento, promoción de cambios |
| **V** | Verificabilidad | Tests, typecheck, lint, calidad automatizada |
| **VI** | Fuente de Verdad | Reconciliación, consistencia |
| **VII** | Primacía del Sistema | Neutralidad de modelo |
| **VIII** | Seguridad Agéntica | Protección, permisos |
| **IX** | Persistencia | Base de datos, estado |
| **X** | Interfaces | Contratos, compatibilidad |
| **XI** | Observabilidad | Auditoría, logs, métricas |
| **XII** | Roles | Capacidades, jurisdicción |
| **XIII** | Primacía Conceptual | Interacción semántica |

## Instalación

La constitución puede leerse sin instalar dependencias. La rama de integración también contiene un linter Python, config kits y diez starters ejecutables; esas herramientas sí requieren sus runtimes y dependencias.

```bash
# Clonar el repositorio
git clone https://github.com/fegome90-cmd/constitucion-ai.git
cd constitucion-ai
```

Para ejecutar el linter y sus pruebas: `uv sync --frozen` y `uv run --frozen pytest tests/ -q`. Para listar los starters: `python3 scripts/scaffold.py --list`. Para **exportar un proyecto utilizable**: `python3 scripts/scaffold.py --template python --name mi-proyecto --output ..`. La auditoría `python3 tooling/audit.py --run-gates` crea proyectos temporales y ejecuta comandos del catálogo; úsala solo con checkouts confiables.

## Uso Rápido

### Opción 1: Referenciar desde tu proyecto

En el `CLAUDE.md` de tu proyecto:

```markdown
## Gobernanza

Este proyecto opera bajo la [Constitución de Código Agéntico](https://github.com/fegome90-cmd/constitucion-ai).

Consultar `constitution/AGENTIC-CONSTITUTION.md` para leyes completas.
```

### Opción 2: Incluir directamente

Copiar `constitution/AGENTIC-CONSTITUTION.md` a tu proyecto.

## Estructura del Proyecto

```
constitucion-ai/
├── constitution/                  # Normas constitucionales y checklist
├── docs/                          # ADR, roles, planes y guías
├── skills/agentic-constitution-anchor/  # Anclaje constitucional
├── scripts/                       # Linter, aplicador y comprobación de versiones
├── tooling/                       # Generación y auditoría de starters
├── templates/                     # Config kits canónicos
├── starters/                      # Diez proyectos ejecutables
├── tests/                         # Regresiones y pruebas de integración
├── evidencia/                      # Informes de ejecución
├── catalog.json                   # Contrato de los diez entornos
├── CLAUDE.md                      # Guía de agentes
└── README.md                      # Este archivo
```

## Desarrollo

### Constitution Linter

Herramienta de linting para detectar violaciones de neutralidad de modelo (Ley VII, Artículo 2).

#### Instalación

```bash
# Instalar como herramienta UV
uv tool install .

# O usar directamente con uv run
uv run constitution-linter --help
```

#### Uso

```bash
# Escanear archivo o directorio
uv run constitution-linter scan .

# Ver plan de correcciones
uv run constitution-linter plan .

# Aplicar correcciones automáticas
uv run constitution-linter fix .

# Ejecutar todo (scan + plan + fix)
uv run constitution-linter run-all .

# Crear un commit de los archivos ya versionados que hayan sido corregidos
uv run constitution-linter run-all . --commit
```

`--commit` no incorpora archivos nuevos sin seguimiento, aunque `fix` los haya modificado o movido. Rechaza cambios previamente preparados en las rutas que intenta corregir, destinos en conflicto y renombres de directorios que contengan reglas `.gitignore` internas. Para esos casos, ejecuta `fix` sin `--commit`, revisa el resultado y confirma manualmente; el commit automático no debe absorber trabajo ajeno. La combinación `run-all --interactive --commit` está prohibida: realiza las correcciones interactivas y el commit en pasos separados.

Las correcciones marcadas como pendientes de revisión no se aplican en modo automático.
Usa `fix --interactive` para aceptar o rechazar cada corrección de contenido y cada renombre.
En modo interactivo, un dry run muestra las correcciones candidatas sin aplicarlas.

El linter utiliza mapas de líneas de CommonMark para proteger los bloques de código Markdown, incluso los anidados en listas y citas. Los archivos de código fuente se escanean sin aplicar la gramática Markdown. `TXT-001` conserva las referencias al componente canónico `CLAUDE.md` delimitadas como rutas o texto, incluidos fragmentos de enlace y referencias numéricas de línea; no exime nombres compuestos ni sufijos de respaldo.

#### Códigos de Salida

| Código | Descripción |
|--------|-------------|
| 0 | Sin violaciones en `scan`, o ejecución correcta de `plan`, `fix` y `run-all` |
| 1 | Violaciones encontradas |
| 2 | Dry run con violaciones |
| 3 | Error de validación |
| 4 | Error de ejecución |

#### Patrones Detectados

| Categoría | Regla | Descripción |
|-----------|-------|-------------|
| Directorios | DIR-001 | `.claude/` → `.ai/` |
| Directorios | DIR-002 | `.cursor/` → `.ai/` |
| Archivos | FILE-001 | `.cursorrules` → `.airules` |
| Archivos | FILE-002 | `.cursorignore` → `.aiignore` |
| Texto | TXT-001 | "Claude" → "AI" |
| Texto | TXT-002 | "cursor rules" → "AI rules" |

> **Nota:** Los patrones están definidos en `scripts/constitution_linter/patterns.py`. Para personalizar, modificar ese archivo o usar `load_patterns_from_yaml()` con un archivo YAML personalizado.

### Linting de Documentación

```bash
# Lint de archivos Markdown
markdownlint-cli2 "**/*.md"
```

## Filosofía

> "El proceso de control no deberá ser más costoso que el riesgo que intenta contener."

Esta constitución busca equilibrio entre:

- **Rigor** vs. **Agilidad**
- **Control** vs. **Autonomía**
- **Trazabilidad** vs. **Overhead**

No es burocracia por burocracia. Es estructura mínima necesaria para trabajar con agentes de forma predecible.

## Versionado

| Versión | Archivo | Estado | Descripción |
|---------|---------|--------|-------------|
| v1.1 | [`constitution/AGENTIC-CONSTITUTION.md`](./constitution/AGENTIC-CONSTITUTION.md) | ✅ Activa | Estructura mejorada, 13 leyes, Anexo III |
| v0.7 | [`archive/v0.7-AGENTIC-CONSTITUTION.md`](./archive/v0.7-AGENTIC-CONSTITUTION.md) | 📁 Archivada | Versión inicial |

## Contribuir

Las contribuciones son bienvenidas. Para proponer cambios:

1. **Abrir issue** con propuesta de enmienda
2. **Discutir** impacto y justificación con la comunidad
3. **Crear PR** con cambios documentados siguiendo el proceso de enmienda del Anexo III
4. **Revisión** según proceso constitucional definido

Ver [`constitution/REVIEW-CHECKLIST.md`](./constitution/REVIEW-CHECKLIST.md) para el proceso de revisión.

## Licencia

MIT - Usa, modifica, comparte libremente.

---

<p align="center">
  <em>"Sin reglas claras, los agentes son herramientas peligrosas. Con ellas, son multiplicadores de capacidad."</em>
</p>
