# Scaffolding opcional como capa separada

Status: accepted
Supersedes: ADR-0002

Se acepta el generador del ZIP auditado como `scripts/scaffold.py`: una capa opcional, separada de los config kits. Crea un proyecto nuevo desde `starters/<lenguaje>/`, renombrando slug y módulo con validación de rutas. `apply-kit.sh` conserva su rol de aplicar configuración a un proyecto existente.

ADR-0002 prohibía cualquier scaffolder porque en ese momento el alcance era solo archivos de configuración. Con la importación de los diez starters, el generador resuelve un problema real sin tocar la capa de configuración: usa Python estándar, sin dependencias externas, y trae sus propios tests. ADR-0002 pasa a estar superseded por esta decisión, no derogada en su espíritu: los config kits siguen siendo archivos estáticos.
