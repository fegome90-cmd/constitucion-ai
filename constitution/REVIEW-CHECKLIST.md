# Checklist de Revisión - Constitución de Código Agéntico v1.0

> Documento fuente: `AGENTIC-CONSTITUTION-v1.0.md`
> Fecha de revisión: 2026-03-14
> Total de chunks: 15 | Líneas: ~1240

---

## Metadatos

- [x] Documento fuente identificado: `AGENTIC-CONSTITUTION-v1.0.md`
- [x] Versión confirmada: 1.0
- [x] Jerarquía interpretativa establecida
- [x] Glosario no contradice definiciones fundamentales

**Estado de Revisión:** ✅ COMPLETADO (2026-03-14)

---

## CHUNK 1: Fundamentos (Líneas 1-48) ✅ REVISADO

**Propósito:** Base interpretativa y definiciones vinculantes

### Preámbulo

- [x] Propósito declarado: proteger trazabilidad, calidad, reversibilidad
- [x] Coherencia arquitectónica verificada
- [x] Verificabilidad del trabajo establecida
- [x] Continuidad del sistema priorizada

### Definiciones Fundamentales (Artículos 1-7)

- [x] **Art. 1 - Mutación:** definida como acción que crea/modifica/elimina artefactos
- [x] **Art. 2 - Tarea:** unidad con objetivo explícito y resultado esperable
- [x] **Art. 3 - Validación:** mecanismo verificable de cumplimiento
- [x] **Art. 4 - Evidencia:** resultado observable y trazable
- [x] **Art. 5 - Fuente de verdad:** artefacto oficial como referencia
- [x] **Art. 6 - Excepción:** desviación explícita y justificada
- [x] **Art. 7 - Riesgo:** clasificación bajo/medio/alto definida

---

## CHUNK 2: Ley I - Cambio Legítimo (Líneas 50-90) ✅ REVISADO

**Propósito:** Regular cuándo una mutación es válida

### Artículos (6)

- [x] **Art. 1:** Intención explícita antes de mutar
- [x] **Art. 2:** Planificación proporcional al riesgo
- [x] **Art. 3:** Validación previa definida
- [x] **Art. 4:** Evidencia obligatoria
- [x] **Art. 5:** Proporcionalidad operativa
- [x] **Art. 6:** Coherencia plan-ejecución-revisión

### Incisos Operativos

- [x] Cambio pequeño = plan breve
- [x] Cambio sistémico = validación fuerte
- [x] No aceptar "debería funcionar"
- [x] Desviaciones deben constar explícitamente

### Casos de Aplicación

- [x] Microfix local: intención + validación mínima
- [x] Cambio de contrato: plan + pruebas + evidencia
- [x] Modificación arquitectónica: análisis + justificación

---

## CHUNK 3: Ley II - Lectura Previa y No Duplicación (Líneas 93-122) ✅ REVISADO

**Propósito:** Impedir reescritura ciega y duplicación

### Artículos (5)

- [x] **Art. 1:** Lectura previa obligatoria
- [x] **Art. 2:** Prioridad de reutilización
- [x] **Art. 3:** Creación justificada
- [x] **Art. 4:** Prohibición de duplicación funcional
- [x] **Art. 5:** Ausencia explícita declarada

### Incisos Operativos

- [x] No crear archivo sin revisar vecinos
- [x] No reescribir documentación viva sin revisar
- [x] No abrir nueva fuente de verdad si existe una

---

## CHUNK 4: Ley III - Arquitectura Base (Líneas 125-177) ✅ REVISADO + ACTUALIZADO

**Propósito:** Establecer doctrina arquitectónica consistente

### Artículos (7)

- [x] **Art. 1:** Arquitectura por defecto adoptada
- [x] **Art. 2:** Disciplina antes que moda
- [x] **Art. 3:** Prohibición de sobreingeniería ornamental
- [x] **Art. 4:** Excepción arquitectónica justificada
- [x] **Art. 5:** Simplicidad estructural
- [x] **Art. 6:** Modularidad y bajo acoplamiento
- [x] **Art. 7:** Regla de Scope ✨ NUEVO (2026-03-14)

### Art. 7 - Regla de Scope (Añadido)

- [x] **Inciso 7.1:** 2+ features → directorios compartidos (`shared/`, `common/`, `core/`)
- [x] **Inciso 7.2:** 1 feature → permanece en directorio de la feature
- [x] **Inciso 7.3:** Dependencias hacia adentro (features dependen de shared, nunca al revés)
- [x] **Incisos operativos:** promoción justificada, sin duplicación, evidencia de uso transversal
- [x] **Casos de aplicación:** Button, LoginForm, Helper temporal

### Patrones Referenciados

- [x] Clean architecture / hexagonal cuando corresponda
- [x] SOLID y enfoques funcionales como base
- [x] Ningún patrón por reflejo o apariencia
- [x] **Scope Rule** (Felipe's meta-framework) integrada

---

## CHUNK 5: Ley IV - Control de Versiones (Líneas 160-210) ✅ REVISADO

**Propósito:** Proteger trazabilidad e integración segura

### Artículos (7)

- [x] **Art. 1:** Base Git obligatoria
- [x] **Art. 2:** Rama identificable por tarea
- [x] **Art. 3:** Worktree aislado (con excepciones definidas)
- [x] **Art. 4:** Commit por tarea
- [x] **Art. 5:** Protección de main
- [x] **Art. 6:** Integración previa
- [x] **Art. 7:** Orden e higiene del trabajo

### Excepciones Worktree (3 condiciones)

- [x] Riesgo bajo
- [x] Superficie local
- [x] Sin posibilidad de conflicto

### Higiene Obligatoria

- [x] Eliminar archivos temporales
- [x] Remover código muerto
- [x] Limpiar imports inútiles
- [x] Excluir artefactos transitorios

---

## CHUNK 6: Ley V - Verificabilidad (Líneas 213-276) ✅ REVISADO

**Propósito:** Validación reproducible, no por intuición

### Artículos (8)

- [x] **Art. 1:** Testeabilidad obligatoria
- [x] **Art. 2:** Calidad automatizada mínima
- [x] **Art. 3:** Gates mínimos (lint, formato, typecheck, tests)
- [x] **Art. 4:** Herramienta sin ejecución no vale
- [x] **Art. 5:** Validación proporcional al riesgo
- [x] **Art. 6:** Determinismo primero
- [x] **Art. 7:** Revisión mínima obligatoria
- [x] **Art. 8:** Niveles de testing según riesgo

### Herramientas por Stack

- [x] Python: Ruff, mypy, pytest, Pyrefly
- [x] Frontend: Biome, suites del stack

### Revisión Manual (3 requisitos)

- [x] Automatización no viable
- [x] Documentar por qué
- [x] Evidencia trazable del criterio

---

## CHUNK 7: Ley VI - Fuente de Verdad (Líneas 279-318) ✅ REVISADO

**Propósito:** Evitar contradicciones entre código, docs y estado

### Artículos (6)

- [x] **Art. 1:** Fuente de verdad explícita
- [x] **Art. 2:** Separación contexto vs trabajo
- [x] **Art. 3:** Prohibición de contradicción viva
- [x] **Art. 4:** Reconciliación obligatoria al cierre
- [x] **Art. 5:** Cierre inválido sin reconciliación
- [x] **Art. 6:** Documentación mínima obligatoria

### Documentación Obligatoria Para

- [x] Cambios de contrato/interfaz
- [x] Comandos nuevos o modificados
- [x] Configuración operativa
- [x] Flujos críticos
- [x] Comportamientos visibles

---

## CHUNK 8: Ley VII - Neutralidad de Modelo (Líneas 321-357) ✅ REVISADO

**Propósito:** Independencia de proveedor/modelo LLM

### Artículos (6)

- [x] **Art. 1:** Primacía del sistema
- [x] **Art. 2:** Neutralidad de modelo (obligatoria salvo justificación)
- [x] **Art. 3:** El modelo es componente, no centro
- [x] **Art. 4:** Contratos por capacidad
- [x] **Art. 5:** Reemplazabilidad
- [x] **Art. 6:** Excepción de optimización (3 requisitos)

### Requisitos Excepción de Optimización

- [x] Beneficio técnico real y demostrable
- [x] Acoplamiento documentado y reversible
- [x] Adapter para sustitución futura

---

## CHUNK 9: Ley VIII - Seguridad Agéntica ⚠️ CRÍTICO (Líneas 360-502)

**Propósito:** Protección contra acciones inseguras y degradación

### Artículos (14)

- [ ] **Art. 1:** Principio de mínimo privilegio
- [ ] **Art. 2:** Acceso explícito y acotado
- [ ] **Art. 3:** Fallo cerrado
- [ ] **Art. 4:** Separación de capacidades
- [ ] **Art. 5:** Mutación alto impacto = control reforzado
- [ ] **Art. 6:** Protección de secretos
- [ ] **Art. 7:** Trazabilidad de acciones sensibles
- [ ] **Art. 8:** Prohibición de auto-expansión silenciosa
- [ ] **Art. 9:** Aislamiento por defecto
- [ ] **Art. 10:** Dependencias confiables
- [ ] **Art. 11:** Seguridad proporcional al riesgo
- [ ] **Art. 12:** Seguridad prevalece sobre conveniencia
- [ ] **Art. 13:** Normas básicas de operación segura
- [ ] **Art. 14:** Aprobación humana para acciones sensibles

### Art. 13 - Normas Básicas (12 incisos)

- [ ] API keys fuera de prompts/commits/logs
- [ ] Mínimo privilegio por defecto
- [ ] Red controlada y justificada
- [ ] Puertos con propósito explícito
- [ ] Separación de entornos
- [ ] Protección contra prompt injection
- [ ] Prohibición de ejecución ciega
- [ ] Descargas como vector de riesgo
- [ ] Restricción de borrado destructivo
- [ ] Logs sin secretos
- [ ] Validación de entradas
- [ ] Fallback seguro

### Art. 14 - Aprobación Humana

- [ ] **14.1 Obligatoria:** producción, secretos, borrados, gobernanza
- [ ] **14.2 Condicional:** contratos, migraciones, integraciones
- [ ] **14.3 Requisitos:** especificidad, trazabilidad, no-expansión
- [ ] **14.4 Mapeo local obligatorio** de autoridades
- [ ] **14.5 Casos de aplicación** documentados

---

## CHUNK 10: Ley IX - Persistencia (Líneas 505-590) ✅ REVISADO

**Propósito:** Regular diseño, uso y protección de datos

### Artículos (17)

- [x] **Art. 1:** Persistencia justificada
- [x] **Art. 2:** BD es parte del sistema
- [x] **Art. 3:** Modelo de datos explícito
- [x] **Art. 4:** Schema versionado
- [x] **Art. 5:** Migraciones obligatorias
- [x] **Art. 6:** Integridad primero
- [x] **Art. 7:** Escritura controlada
- [x] **Art. 8:** Separación de entornos de datos
- [x] **Art. 9:** Acceso por mínimo privilegio
- [x] **Art. 10:** Cambios destructivos = alto riesgo
- [x] **Art. 11:** Respaldo y recuperación
- [x] **Art. 12:** Observabilidad de persistencia
- [x] **Art. 13:** Consultas deliberadas
- [x] **Art. 14:** Compatibilidad consciente
- [x] **Art. 15:** Datos sensibles minimizados
- [x] **Art. 16:** Semillas/fixtures controlados
- [x] **Art. 17:** Reconciliación código-datos

---

## CHUNK 11: Ley X - Contratos (Líneas 593-634) ✅ REVISADO

**Propósito:** Proteger estabilidad entre componentes

### Artículos (8)

- [x] **Art. 1:** Contrato explícito
- [x] **Art. 2:** Alcance del contrato (entradas, salidas, errores)
- [x] **Art. 3:** Prohibición de interfaces implícitas críticas
- [x] **Art. 4:** Cambio de contrato = sensible
- [x] **Art. 5:** Compatibilidad hacia atrás
- [x] **Art. 6:** Deprecación previa a remoción
- [x] **Art. 7:** Transición controlada
- [x] **Art. 8:** Contrato y validación alineados

### Tipos de Contrato

- [x] API HTTP
- [x] CLI
- [x] Funciones
- [x] Eventos
- [x] Esquemas
- [x] Prompts estructurados

---

## CHUNK 12: Ley XI - Observabilidad (Líneas 637-678) ✅ REVISADO

**Propósito:** Sistema observable, auditable, evaluable

### Artículos (8)

- [x] **Art. 1:** Observabilidad mínima obligatoria
- [x] **Art. 2:** Evidencia operativa proporcional
- [x] **Art. 3:** Distinción éxito aparente vs estado sano
- [x] **Art. 4:** Trazabilidad de acciones relevantes
- [x] **Art. 5:** Auditoría posible
- [x] **Art. 6:** Señales antes que relato
- [x] **Art. 7:** Observabilidad segura
- [x] **Art. 8:** Evidencia de cierre

---

## CHUNK 13: Ley XII - Roles, Capacidades y Jurisdicción (NUEVA) ✅ REVISADO

**Propósito:** Definir quién puede hacer qué, sobre qué superficies, bajo qué condiciones

### Artículos (6)

- [x] **Art. 1:** Definiciones fundamentales (rol, capacidad, acto técnico, superficie, jurisdicción, veredicto)
- [x] **Art. 2:** Principio de jurisdicción explícita
- [x] **Art. 3:** Separación de capacidades (6 capacidades base)
- [x] **Art. 4:** Roles base del sistema (6 roles MVP)
- [x] **Art. 5:** Prohibiciones (auto-elevación, prepare-review-approve mismo agente)
- [x] **Art. 6:** Superficies y niveles de riesgo

### Roles MVP

- [x] `reader`: Solo lectura y análisis
- [x] `editor`: Desarrollo estándar
- [x] `reviewer`: Revisión de código
- [x] `sensitive-operator`: Operaciones sensibles
- [x] `maintainer`: Mantenimiento del sistema
- [x] `human-approver`: Aprobación humana

### Capacidades Base

- [x] `read`: Leer archivos (low risk)
- [x] `write`: Modificar código (medium risk)
- [x] `review`: Revisar PRs (low risk)
- [x] `sensitive_op`: BD, credenciales (high risk)
- [x] `govern`: Políticas, roles (critical risk)
- [x] `approve`: Aprobar acciones (critical risk)

### Integración con Ley VIII

- [x] Complementa régimen de aprobación humana
- [x] Roles definen quién puede iniciar acciones
- [x] Ley VIII define cuándo requiere aprobación adicional

---

## CHUNK 13: Régimen de Excepciones (Líneas 681-759) ✅ REVISADO

**Propósito:** Controlar desviaciones temporales

### Artículos (8)

- [x] **Art. 1:** Excepción explícita (qué regla no aplica)
- [x] **Art. 2:** Justificación mínima (por qué, riesgo, beneficio, control)
- [x] **Art. 3:** Alcance acotado (qué, cuánto, hasta cuándo)
- [x] **Art. 4:** Autoridad de aprobación (4 niveles)
- [x] **Art. 5:** Responsable y revisión
- [x] **Art. 6:** Temporal por defecto (máx 30 días)
- [x] **Art. 7:** No conversión automática en regla (>3 veces)
- [x] **Art. 8:** Cierre de excepción

### Niveles de Autoridad

- [x] **Bajo riesgo:** cualquier miembro responsable
- [x] **Medio riesgo:** lead técnico
- [x] **Alto riesgo:** arquitecto/responsable proyecto
- [x] **Seguridad:** responsable de seguridad

---

## CHUNK 14: Interpretación + Anexos (Líneas 762-1006) ✅ REVISADO

### Interpretación General

- [x] **Art. 1:** Espíritu de la constitución (6 principios)
- [x] **Art. 2:** Regla de conflicto (seguridad > conveniencia)
- [x] **Art. 3:** Regla anti-burocracia (proporcionalidad)

### Anexo I: CLOOP (7 Fases)

- [x] **Fase 1 - Clarify:** comprender antes de mutar
- [x] **Fase 2 - Layout:** planificar antes de ejecutar
- [x] **Fase 3 - Operate:** ejecutar aislado y controlado
- [x] **Fase 4 - Observe:** verificar comportamiento real
- [x] **Fase 5 - Reflect:** mejorar antes de cerrar
- [x] **Fase 6 - Reconcile:** cerrar sin contradicciones
- [x] **Fase 7 - Handoff:** dejar listo para continuidad

### Anexo II: Mapa de Enforcement

- [x] **Categoría A:** Validación automática
- [x] **Categoría B:** Revisión humana obligatoria
- [x] **Categoría C:** Evidencia documental
- [x] **Categoría D:** Auditoría posterior
- [x] **Mapa por familia de normas** (11 leyes + excepciones)

### Estado de Versión

- [x] Endurecimientos documentados
- [x] Ambigüedades reducidas
- [x] Lenguaje normativo homogeneizado

---

## CHUNK 15: Glosario (Líneas 1009-1241) ✅ REVISADO

**75 términos definidos**

### Verificación de Integridad

- [x] Sin contradicciones con Definiciones Fundamentales
- [x] Términos técnicos cubiertos (sistema, agente, código agéntico)
- [x] Términos operativos cubiertos (commit, worktree, gate)
- [x] Términos de seguridad cubiertos (secreto, prompt injection, fallo cerrado)
- [x] Términos de proceso cubiertos (trazabilidad, reconciliación, cierre)

### Términos Clave a Verificar

- [x] #1 Sistema
- [x] #2 Código agéntico
- [x] #3 Agente
- [x] #53 Fallo cerrado
- [x] #65 Prompt injection
- [x] #71 Aprobación humana
- [x] #73 Proporcionalidad

---

## Resumen de Progreso

| Fase | Chunks | Estado |
|------|--------|--------|
| 1. Fundamentos | 1 | ✅ COMPLETADO |
| 2. Leyes Sustantivas | 2-7 | ✅ COMPLETADO |
| 3. Seguridad (Crítico) | 8-9 | ✅ COMPLETADO |
| 4. Contratos/Observabilidad | 10-12 | ✅ COMPLETADO |
| 5. Régimen Operativo | 13-14 | ✅ COMPLETADO |
| 6. Referencia | 15 | ✅ COMPLETADO |

**Total:** 15 chunks | 11 leyes | ~101 artículos | 75 términos glosario

---

## Notas de Revisión

```
[2026-03-14 16:30] MODIFICACIÓN: Artículo 7 (Regla de Scope) añadido a Ley III
- Inciso 7.1: 2+ features → shared/common/core
- Inciso 7.2: 1 feature → local
- Inciso 7.3: Dependencias hacia adentro
- Incisos operativos y casos de aplicación incluidos
- Motivo: Alineación con metodología Felipe (Scope Rule obligatoria)

[2026-03-14] Revisión completa del documento AGENTIC-CONSTITUTION-v1.0.md

OBSERVACIONES:
1. CHUNK 1 (Fundamentos): Estructura sólida. Jerarquía interpretativa clara.
2. CHUNK 2-7 (Leyes I-VI): Coherencia entre artículos, incisos y casos de aplicación.
3. CHUNK 8-9 (Leyes VII-VIII): Neutralidad de modelo y seguridad agéntica bien desarrolladas.
4. CHUNK 9 (Ley VIII - Seguridad): 14 artículos, el más extenso. Art. 14 sobre aprobación humana muy detallado.
5. CHUNK 10 (Ley IX - Persistencia): 17 artículos, el segundo más extenso. Cubre todos los aspectos de BD.
6. CHUNK 11-12 (Leyes X-XI): Contratos y observabilidad complementan bien las otras leyes.
7. CHUNK 13 (Excepciones): Régimen claro con niveles de autoridad definidos.
8. CHUNK 14 (Anexos): CLOOP es un workflow operativo de 7 fases muy bien estructurado.
9. CHUNK 15 (Glosario): 75 términos sin contradicciones con definiciones fundamentales.

HALLAZGOS:
- Documento de alta calidad, bien estructurado y coherente
- Lenguaje normativo consistente ("deberá" vs "podrá")
- Casos de aplicación concretos y útiles
- Cumplimiento de endurecimientos declarados en sección "Estado de esta versión"

RECOMENDACIÓN: Documento listo para adopción como v1.0
```
