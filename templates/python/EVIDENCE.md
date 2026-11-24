# Evidencia de la evidence bar — kit Python

Relevamiento del 17 de noviembre de 2026. Barra: ≥1M descargas semanales o ≥5k estrellas, y actividad en los últimos seis meses. Un `NO PASA` no se oculta. Los números salen de PyPI/GitHub; Context7 se usó solo para contrastar la sintaxis de configuración y confirmar que existe documentación accesible.

| Herramienta | Versión | Adopción | Actividad | Fuente | Estado |
| --- | --- | --- | --- | --- | --- |
| uv | 0.13.9 | 50.954.411 desc/sem | release 2026-11-17, [commit 2026-11-17](https://github.com/astral-sh/uv/commit/7f396534d58321e60b5ba204151326712d912ece) | PyPI, GitHub `astral-sh/uv` | PASA |
| hatchling | 1.33.0 | 96.945.340 desc/sem | release 2026-10-28, [commit 2026-11-08](https://github.com/pypa/hatch/commit/893fa13ccd6129550194a4964c22c1cc6b63bc0d), `★7.253` | PyPI, GitHub `pypa/hatch` | PASA |
| ruff | 0.17.5 | 102.813.494 desc/sem | release 2026-11-12, [commit 2026-11-17](https://github.com/astral-sh/ruff/commit/45f24aea1242cb685014fefd1927eba517a26e7c) | PyPI, GitHub `astral-sh/ruff` | PASA |
| mypy | 2.4.1 | 48.553.627 desc/sem | release 2026-10-28, [commit 2026-11-17](https://github.com/python/mypy/commit/22b03fed047204e80a76921957ab8b5f3b4d2896) | PyPI, GitHub `python/mypy` | PASA |
| pytest | 9.2.0 | 239.009.779 desc/sem | release 2026-10-27, [commit 2026-11-17](https://github.com/pytest-dev/pytest/commit/560c86cd103dd87bb873aad3c1b0f76a4eee5931) | PyPI, GitHub `pytest-dev/pytest` | PASA |
| bandit *(extra opcional)* | 1.9.4 | 7.231.128 desc/sem | release 2026-02-25, [commit 2026-11-09](https://github.com/PyCQA/bandit/commit/2d5467c45c3189f4d7d07e8022276bc73a478abd) | PyPI, GitHub `PyCQA/bandit` | PASA |

La actividad por commits fue corroborada el 24 de noviembre de 2026 mediante la API de GitHub, con corte al 17 de noviembre de 2026 (23:59:59 UTC). Los enlaces fijan el commit observado en la rama por defecto de cada repositorio; no se infiere actividad a partir de la fecha de release. Todas superan el umbral de adopción y mantenimiento. Bandit tiene un release fechado fuera de la ventana, pero registra commits recientes en GitHub y queda documentado solo como extra opcional fuera del mínimo base.

`uv 0.13.9` se publicó el mismo día del relevamiento, sin tiempo de soak. Queda registrado como deuda a reevaluar en el primer recheck de versiones (ver ADR-0003).
