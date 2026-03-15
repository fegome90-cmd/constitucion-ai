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

### Requisitos

- Python >= 3.12
- uv (recomendado) o pip

### Setup

```bash
# Clonar el repositorio
git clone https://github.com/felipe/constitucion-ai.git
cd constitucion-ai

# Crear entorno virtual
uv venv
source .venv/bin/activate  # Linux/Mac
# o: .venv\Scripts\activate  # Windows

# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"
```

## Uso Rápido

### Opción 1: Referenciar desde tu proyecto

En el `CLAUDE.md` de tu proyecto:

```markdown
## Gobernanza

Este proyecto opera bajo la [Constitución de Código Agéntico](https://github.com/felipe/constitucion-ai).

Consultar `constitution/AGENTIC-CONSTITUTION.md` para leyes completas.
```

### Opción 2: Incluir directamente

Copiar `constitution/AGENTIC-CONSTITUTION.md` a tu proyecto.

## Estructura del Proyecto

```
constitucion-ai/
├── constitution/
│   ├── AGENTIC-CONSTITUTION.md    # Constitución activa (v1.1)
│   └── REVIEW-CHECKLIST.md        # Checklist de revisión
├── docs/
│   ├── mandate-roles-and-jurisdiction.md
│   └── reviewctl-agent-guide.md
├── archive/
│   ├── v1.0-AGENTIC-CONSTITUTION.md  # Versiones anteriores
│   └── v0.7-AGENTIC-CONSTITUTION.md
├── scripts/
│   └── reviewctl/                 # Utilidades de revisión
│       └── lint_markdownlint_changed.sh
├── .reviewctl/
│   └── project-gates.json         # Configuración de gates
├── CLAUDE.md                      # Contexto para Claude Code
├── pyproject.toml                 # Configuración del proyecto
└── README.md                      # Este archivo
```

## Desarrollo

### Linting y Formato

```bash
# Ejecutar todos los linters
./scripts/lint-all.sh

# O individualmente
ruff check .
ruff format .
mypy .
bandit -r .
codespell
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
| v1.0 | [`archive/v1.0-AGENTIC-CONSTITUTION.md`](./archive/v1.0-AGENTIC-CONSTITUTION.md) | 📁 Archivada | Versión base con 7 leyes |
| v0.7 | [`archive/v0.7-AGENTIC-CONSTITUTION.md`](./archive/v0.7-AGENTIC-CONSTITUTION.md) | 📁 Archivada | Versión inicial |

## Contribuir

Las contribuciones son bienvenidas. Para proponer cambios:

1. **Abrir issue** con propuesta de enmienda
2. **Discutir** impacto y justificación con la comunidad
3. **Crear PR** con cambios documentados siguiendo el proceso de enmienda del Anexo III
4. **Revisión** según proceso constitucional definido

Ver [`constitution/REVIEW-CHECKLIST.md`](./constitution/REVIEW-CHECKLIST.md) para el proceso de revisión.

## Licencia

MIT - Usa, modifica, comparte libres.

---

<p align="center">
  <em>"Sin reglas claras, los agentes son herramientas peligrosas. Con ellas, son multiplicadores de capacidad."</em>
</p>
