# Constitución de Código Agéntico

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

## Las 7 Leyes

| Ley | Nombre | Propósito |
|-----|--------|-----------|
| I | Cambio Legítimo | Toda mutación requiere intención explícita, planificación proporcional, evidencia |
| II | Lectura Previa | Leer antes de escribir. No duplicar. |
| III | Control de Agentes | Subprocesos y agentes requieren supervisión |
| IV | Validación y Revisión | Todo cambio debe ser verificable |
| V | Gobernanza | Zonas de riesgo, permisos, excepciones |
| VI | Gestión de Estado | Coherencia entre sesiones |
| VII | Comunicación | Trazabilidad y documentación |

## Uso Rápido

### Opción 1: Referenciar

En el `CLAUDE.md` de tu proyecto:

```markdown
## Gobernanza

Este proyecto opera bajo la [Constitución de Código Agéntico](https://github.com/felipe/constitucion-ai).

Consultar `constitution/AGENTIC-CONSTITUTION.md` para leyes completas.
```

### Opción 2: Incluir

Copiar `constitution/AGENTIC-CONSTITUTION.md` directamente a tu proyecto.

## Estructura del Repo

```
constitucion-ai/
├── constitution/
│   ├── AGENTIC-CONSTITUTION.md    # Constitución activa (v1.0)
│   └── REVIEW-CHECKLIST.md        # Checklist de revisión
├── archive/
│   └── v0.7-AGENTIC-CONSTITUTION.md  # Versiones anteriores
├── docs/
│   └── mandate-roles-and-jurisdiction.md
├── CLAUDE.md                      # Contexto para Claude Code
└── README.md                      # Este archivo
```

## Filosofía

> "El proceso de control no deberá ser más costoso que el riesgo que intenta contener."

Esta constitución busca equilibrio entre:

- **Rigor** vs. **Agilidad**
- **Control** vs. **Autonomía**
- **Trazabilidad** vs. **Overhead**

No es burocracia por burocracia. Es estructura mínima necesaria para trabajar con agentes de forma predecible.

## Versionado

| Versión | Archivo | Estado |
|---------|---------|--------|
| v1.0 | `constitution/AGENTIC-CONSTITUTION.md` | Activa |
| v0.7 | `archive/v0.7-AGENTIC-CONSTITUTION.md` | Archivada |

## Contribuir

1. Abrir issue con propuesta de enmienda
2. Discutir impacto y justificación
3. PR con cambios documentados
4. Revisión según proceso constitucional

## Licencia

MIT - Usa, modifica, comparte libremente.

---

*"Sin reglas claras, los agentes son herramientas peligrosas. Con ellas, son multiplicadores de capacidad."*
