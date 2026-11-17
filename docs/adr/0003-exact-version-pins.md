# Pins exactos en los config kits

Status: accepted

Los archivos de los config kits expresan versiones exactas (`ruff==0.17.5`, `mypy==2.4.1`), no mínimos (`ruff>=0.9.0`), aunque `pyproject.toml` de este repo use mínimos hoy.

Un config kit es una receta reproducible: dos personas que lo apliquen deben obtener el mismo entorno. Los mínimos son apropiados para la dependencia declarada de una librería, pero acá el artefacto es la configuración misma, y el smoke test valida ese conjunto exacto.

Consecuencia aceptada: uv 0.13.9 se publicó el mismo día del relevamiento (2026-11-17), así que el pin no tiene tiempo de soak. Se reevaluará en el primer recheck de versiones.
