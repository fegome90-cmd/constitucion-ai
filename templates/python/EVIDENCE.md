# Evidencia de la evidence bar — kit Python

Relevamiento del 17 de noviembre de 2026. Barra: ≥1M descargas semanales o ≥5k estrellas, y actividad en los últimos seis meses. Un `NO PASA` no se oculta. Los números salen de PyPI/GitHub; Context7 se usó solo para contrastar la sintaxis de configuración y confirmar que existe documentación accesible.

| Herramienta | Versión | Adopción | Actividad | Fuente | Estado |
| --- | --- | --- | --- | --- | --- |
| uv | 0.13.9 | 50.954.411 desc/sem | release 2026-11-17 | PyPI, GitHub `astral-sh/uv` | PASA |
| hatchling | 1.33.0 | 96.945.340 desc/sem | release 2026-10-28, commits 2026-11-08 (`★7.253`) | PyPI, GitHub `pypa/hatch` | PASA |
| ruff | 0.17.5 | 102.813.494 desc/sem | release 2026-11-12 | PyPI, GitHub `astral-sh/ruff` | PASA |
| mypy | 2.4.1 | 48.553.627 desc/sem | release 2026-10-28 | PyPI, GitHub `python/mypy` | PASA |
| pytest | 9.2.0 | 239.009.779 desc/sem | release 2026-10-27 | PyPI, GitHub `pytest-dev/pytest` | PASA |
| bandit *(extra opcional)* | 1.9.4 | 7.231.128 desc/sem | release 2026-02-25, commits recientes | PyPI, GitHub `PyCQA/bandit` | PASA |

Todas superan el umbral de adopción y mantenimiento. Bandit tiene un release fechado fuera de la ventana, pero registra commits recientes en GitHub y queda documentado solo como extra opcional fuera del mínimo base.

`uv 0.13.9` se publicó el mismo día del relevamiento, sin tiempo de soak. Queda registrado como deuda a reevaluar en el primer recheck de versiones (ver ADR-0003).
