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

## Autoridades de Aprobación

> Cumplimiento de Ley VIII, Art. 14.4 — Mapeo obligatorio de autoridades operativas. Este bloque actúa como fuente operativa en ausencia de `GOVERNANCE.md` en la raíz del repositorio.

### Roles y funciones autorizadas

| Rol / Función | Descripción |
|---------------|-------------|
| **Maintainer** | Mantenedores del repositorio con acceso de escritura directo |
| **Security Lead** | Responsable de revisar cambios con impacto en seguridad |
| **Release Manager** | Responsable de aprobar y publicar nuevas versiones |

### Niveles de autoridad por tipo de acción

| Tipo de acción | Superficie | Autoridad mínima requerida | Umbral de escalación |
|----------------|------------|---------------------------|----------------------|
| Cambios de documentación | `docs/`, `CLAUDE.md` | Maintainer (1 aprobación en PR) | — |
| Enmiendas constitucionales (parche) | `constitution/` | Maintainer (1 aprobación en PR) | — |
| Enmiendas constitucionales (menor/mayor) | `constitution/` | Maintainer (2 aprobaciones en PR) | Security Lead si impacta seguridad |
| Operaciones sobre credenciales o secretos | `.env`, secrets | Security Lead | Maintainer + Security Lead |
| Publicación de release | tags, releases | Release Manager | Maintainer + Release Manager |
| Cambios en políticas de roles | `_ctx/policy/` | Maintainer + Security Lead | Revisión de todos los Maintainers |

### Mecanismo de registro de aprobaciones

- **Cambios de código y documentación:** Aprobación registrada como revisión aprobatoria en el Pull Request de GitHub (mínimo una aprobación antes de merge).
- **Operaciones sensibles:** Entrada en el log de auditoría del repositorio (`git log` con firma de commit) y anotación en el PR o issue correspondiente.
- **Releases:** Tag con firma GPG del Release Manager, más aprobación registrada en la release de GitHub con timestamp.
- **Registro de excepciones:** Anotación explícita en el issue o PR que acoge la excepción, referenciando el régimen de excepciones (Ley VIII, Art. 14, Anexo III).

## Contribuir

Esta constitución es un documento vivo. Proponer cambios vía issues o PRs siguiendo el proceso de enmienda definido en **Anexo III** (`constitution/AGENTIC-CONSTITUTION.md`).

## Licencia

MIT
