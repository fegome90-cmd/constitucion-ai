# Ley XII: Roles, Capacidades y Jurisdicción Operativa

> Guía operativa complementaria a la [Constitución v1.0, Ley XII](../AGENTIC-CONSTITUTION-v1.0.md#ley-xii-roles-capacidades-y-jurisdicción-operativa)

## Propósito

Este documento proporciona:
1. **Diagrama de flujo** del modelo de jurisdicción
2. **Tablas de referencia rápida** para permisos por superficie
3. **Guía de implementación** para el sistema de roles

Para definiciones normativas completas, ver la Constitución.

---

## Modelo Conceptual

```
ROL ──────► CAPACIDAD ──────► ACTO TÉCNICO ──────► VEREDICTO

reader      read            leer archivo         ALLOW
editor      write           modificar            ALLOW
reviewer    review          revisar PR           WARN
sensitive-operator  sensitive_op    borrar tabla   REQUIRE_APPROVAL
maintainer  govern          cambiar policy       ALLOW
human-approver      approve         aprobar acción  WARN (checkpoint)
```

---

## Referencia Rápida: Permisos por Superficie

### Rol Reader
| Superficie | Permiso |
|------------|---------|
| src/, docs/, tests/ | ALLOW |
| _ctx/ | ALLOW |
| _ctx/policy/ | ALLOW |
| vault/ | ALLOW |
| .env | DENY |
| database | DENY |

### Rol Editor
| Superficie | Permiso |
|------------|---------|
| src/, docs/, tests/ | ALLOW |
| _ctx/ | ALLOW |
| _ctx/policy/ | WARN |
| .env | WARN |
| database | DENY |

### Rol Sensitive-Operator
| Superficie | Permiso |
|------------|---------|
| .env | WARN |
| database | REQUIRE_APPROVAL |
| credentials | REQUIRE_APPROVAL |
| production_secrets | DENY |
| _ctx/policy/ | WARN |

### Rol Maintainer
| Superficie | Permiso |
|------------|---------|
| * | ALLOW |
| _ctx/policy/ | ALLOW |
| .env | WARN |
| database | WARN |

---

## Tabla de Jurisdicción (Resumen)

| Rol | Capacidad Crítica | Superficie | Veredicto |
|-----|-------------------|------------|-----------|
| reader | read | .env | DENY |
| editor | write | _ctx/policy/ | REQUIRE_APPROVAL |
| editor | write | .env | WARN |
| sensitive-operator | sensitive_op | database | REQUIRE_APPROVAL |
| maintainer | sensitive_op | database | REQUIRE_APPROVAL |

Ver `_ctx/policy/roles.yaml` para mapeo completo de 200+ superficies.

---

## Implementación

### Configuración
Los roles se definen en: `_ctx/policy/roles.yaml`

### Integración con Ley VIII
- **Roles** → Definen QUIÉN puede iniciar acciones
- **Ley VIII, Art. 14** → Define CUÁNDO requiere aprobación humana adicional
- Ver [Ley VIII](../AGENTIC-CONSTITUTION-v1.0.md#ley-viii-seguridad-agéntica) para el régimen completo de aprobación humana

---

## Referencias

- [Constitución de Código Agéntico v1.0 - Ley XII](../AGENTIC-CONSTITUTION-v1.0.md#ley-xii-roles-capacidades-y-jurisdicción-operativa)
- [Ley VIII, Art. 14 - Aprobación humana](../AGENTIC-CONSTITUTION-v1.0.md#artículo-14-aprobación-humana)
- `_ctx/policy/roles.yaml` - Configuración de roles
