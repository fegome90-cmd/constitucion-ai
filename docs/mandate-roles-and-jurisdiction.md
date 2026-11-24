# Ley XII: Roles, Capacidades y Jurisdicción Operativa

> Guía operativa complementaria a la [Constitución v1.1, Ley XII](../constitution/AGENTIC-CONSTITUTION.md#ley-xii-roles-capacidades-y-jurisdicción-operativa)

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
| .env | BLOCK |
| database | BLOCK |

### Rol Editor

| Superficie | Permiso |
|------------|---------|
| src/, docs/, tests/ | ALLOW |
| _ctx/ | ALLOW |
| _ctx/policy/ | WARN |
| .env | WARN |
| database | BLOCK |

### Rol Sensitive-Operator

| Superficie | Permiso |
|------------|---------|
| .env | WARN |
| database | REQUIRE_APPROVAL |
| credentials | REQUIRE_APPROVAL |
| production_secrets | BLOCK |
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
| reader | read | .env | BLOCK |
| editor | write | _ctx/policy/ | REQUIRE_APPROVAL |
| editor | write | .env | WARN |
| sensitive-operator | sensitive_op | database | REQUIRE_APPROVAL |
| maintainer | sensitive_op | database | REQUIRE_APPROVAL |

`_ctx/policy/roles.yaml` es la ruta exigida por Ley XII para los sistemas que la implementen; no existe un motor de autorización ejecutable ni un catálogo de 200+ superficies en este repositorio. Esta tabla es orientativa, no un control de acceso efectivo.

---

## Implementación

### Configuración

En un sistema que implemente la Ley XII, los roles y el mapeo de superficies deben documentarse en `_ctx/policy/roles.yaml` (artículos 2 y 6). Aquí solo se documenta el contrato conceptual; este repositorio no implementa el motor de autorización.

### Integración con Ley VIII

- **Roles** → Definen QUIÉN puede iniciar acciones
- **Ley VIII, Art. 14** → Define CUÁNDO requiere aprobación humana adicional
- Ver [Ley VIII](../constitution/AGENTIC-CONSTITUTION.md#ley-viii-de-la-seguridad-agéntica) para el régimen completo de aprobación humana

---

## Referencias

- [Constitución de Código Agéntico v1.1 - Ley XII](../constitution/AGENTIC-CONSTITUTION.md#ley-xii-roles-capacidades-y-jurisdicción-operativa)
- [Ley VIII, Art. 14 - Aprobación humana](../constitution/AGENTIC-CONSTITUTION.md#artículo-14-aprobación-humana-para-acciones-sensibles)
- `_ctx/policy/roles.yaml` - Ruta requerida por Ley XII; no implementada en este repositorio
