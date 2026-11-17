# Evidencia de la evidence bar — kit Python

Relevamiento del 17 de noviembre de 2026. Los números salen del registry de cada ecosistema; Context7 se usó solo para contrastar la sintaxis de configuración y confirmar que existe documentación accesible.

| Herramienta | Versión | Downloads/semana | Último release | Actividad ≤6m | Fuente |
| ------------- | --------- | ------------------ | ---------------- | --------------- | -------- |
| uv | 0.13.9 | 50.954.411 | 2026-11-17 | sí | PyPI, GitHub `astral-sh/uv` |
| ruff | 0.17.5 | 102.813.494 | 2026-11-12 | sí | PyPI, GitHub `astral-sh/ruff` |
| mypy | 2.4.1 | 48.553.627 | 2026-10-28 | sí | PyPI, GitHub `python/mypy` |
| pytest | 9.2.0 | 239.009.779 | 2026-10-27 | sí | PyPI, GitHub `pytest-dev/pytest` |
| bandit | 1.9.4 | 7.231.128 | 2026-02-25 | sí (commits) | PyPI, GitHub `PyCQA/bandit` |
| PyYAML | 6.0.3 | 303.302.987 | 2025-09-25 | sí (commits) | PyPI, GitHub `yaml/pyyaml` |

Todas superan el umbral de adopción (≥1M descargas semanales o ≥5k estrellas) y el de mantenimiento (actividad de commits en los últimos seis meses).

Bandit y PyYAML tienen releases fechados fuera de la ventana, pero commits recientes: por el criterio de actividad de commits pasan la barra. Bandit queda documentado como extra opcional, no como parte del mínimo; PyYAML es dependencia de librería, no una herramienta del kit.

`uv 0.13.9` se publicó el mismo día del relevamiento, sin tiempo de soak. Queda registrado como deuda a reevaluar en el primer recheck de versiones (ver ADR-0003).
