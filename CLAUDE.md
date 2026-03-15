# Constitucion AI

Framework de leyes y estructura de estado para trabajo agéntico con Claude Code.

## Propósito

Este proyecto define la "constitución" que regula cómo los agentes de IA deben operar dentro de un sistema de desarrollo de software. Establece:

- **Leyes fundacionales** para cambio legítimo, validación, y gobernanza
- **Estructura de estado** para mantener coherencia entre sesiones
- **Procedimientos operativos** para planificación, ejecución y revisión

## Estructura

```
constitucion-ai/
├── constitution/
│   ├── AGENTIC-CONSTITUTION.md    # Versión activa (v1.0)
│   └── REVIEW-CHECKLIST.md        # Checklist de revisión
├── archive/
│   └── v0.7-AGENTIC-CONSTITUTION.md  # Versiones anteriores
├── docs/
│   └── mandate-roles-and-jurisdiction.md
└── CLAUDE.md                      # Este archivo
```

## Uso con Claude Code

Para usar esta constitución en un proyecto:

1. **Referenciar desde CLAUDE.md del proyecto:**
   ```markdown
   # Gobernanza
   Este proyecto opera bajo la Constitución de Código Agéntico.
   Ver: https://github.com/felipe/constitucion-ai
   ```

2. **O incluir directamente:**
   Copiar `constitution/AGENTIC-CONSTITUTION.md` al proyecto.

## Principios Clave

| Ley | Propósito |
|-----|-----------|
| Ley I | Cambio legítimo - intención explícita, planificación proporcional |
| Ley II | Lectura previa y no duplicación |
| Ley III | Control de agentes y subprocesos |
| Ley IV | Validación y revisión |
| Ley V | Gobernanza de mutaciones |
| Ley VI | Gestión de estado |
| Ley VII | Comunicación y trazabilidad |

## Versionado

- **v1.0** (actual) - `constitution/AGENTIC-CONSTITUTION.md`
- **v0.7** (archivada) - `archive/v0.7-AGENTIC-CONSTITUTION.md`

## Contribuir

Esta constitución es un documento vivo. Proponer cambios via issues o PRs siguiendo el proceso de enmienda definido en la constitución.

## Licencia

MIT
