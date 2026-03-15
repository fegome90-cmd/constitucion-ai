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
│   ├── AGENTIC-CONSTITUTION.md    # Versión activa (v1.1)
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
| Ley III | Arquitectura base y regla de scope |
| Ley IV | Control de versiones, aislamiento y promoción de cambios |
| Ley V | Verificabilidad y calidad automatizada |
| Ley VI | Fuente de verdad y reconciliación |
| Ley VII | Primacía del sistema y neutralidad de modelo |
| Ley VIII | Seguridad agéntica |
| Ley IX | Base de datos y persistencia |
| Ley X | Contratos, interfaces y compatibilidad |
| Ley XI | Observabilidad, auditoría y evidencia operativa |
| Ley XII | Roles, capacidades y jurisdicción operativa |
| Ley XIII | Primacía conceptual en la interacción |

## Versionado

- **v1.1** (actual) - `constitution/AGENTIC-CONSTITUTION.md`
- **v1.0** (archivada) - `archive/v1.0-AGENTIC-CONSTITUTION.md`
- **v0.7** (archivada) - `archive/v0.7-AGENTIC-CONSTITUTION.md`

## Contribuir

Esta constitución es un documento vivo. Proponer cambios via issues o PRs siguiendo el proceso de enmienda definido en **Anexo III** (`constitution/AGENTIC-CONSTITUTION.md`).

El proceso define tres tipos de enmienda (parche, menor, mayor) con criterios de deliberación, aprobación y versionado proporcionales al impacto.

## Licencia

MIT
