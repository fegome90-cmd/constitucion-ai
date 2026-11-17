# Auditoría de integración del 17 de noviembre de 2026

## Dictamen

La ejecución de los starters obtuvo **65 PASS, 0 FAIL y 0 SKIP** en macOS arm64. La validación de adopción de herramientas sigue **PARCIAL** por la excepción de Lua y Maven.

## Evidencia de ejecución

El [readiness report actual](evidencia/readiness-current.json) registra los comandos, códigos de salida y extractos de la ejecución de `setup` y `check` para los diez starters. Cada ejecución partió de una exportación temporal desde `scripts/scaffold.py`. Los siete lockfiles comprobados conservaron su SHA-256.

- Python ejecutó Ruff, mypy, pytest y el build con uv.
- TypeScript, React y CSS ejecutaron sus checks con instalación congelada de pnpm. Los setups omiten scripts de instalación de dependencias.
- Playwright ejecutó un test en Chromium. Puppeteer ejecutó dos tests unitarios y abrió Chrome con el programa compilado.
- Rust ejecutó fmt, Clippy, tests y build con el toolchain fijado. Go ejecutó vet, tests y build.
- Java ejecutó Spotless y Maven Verify con dos tests JUnit. Lua ejecutó StyLua y Busted.

Podés reproducir el informe con `python3 tooling/audit.py --run-gates --output /tmp/readiness.json` desde un checkout de confianza con los runtimes del catálogo. Sin `--run-gates`, el informe solo toma evidencia estructural y registra los gates como `SKIP`.

## Consistencia de versiones

Cada descriptor de pins del catálogo se declara en `templates/`. El starter enlaza ese archivo y conserva su lockfile cuando aplica. `bash scripts/check-versions.sh` devuelve código 1 cuando falta una fuente, el pin no es exacto, el starter no apunta al descriptor canónico o el dato de registry difiere. Una diferencia de versión queda visible sin modificar el pin.

## Excepción a la evidence bar

El mantenedor aceptó conservar las herramientas siguientes el 17 de noviembre de 2026. Las fichas de evidencia mantienen el estado `NO PASA` para la adopción.

- [Lua](templates/lua/EVIDENCE.md) conserva Busted, StyLua, LuaLS y LuaRocks.
- [Java](templates/java/EVIDENCE.md) conserva Maven Compiler Plugin y Maven Surefire Plugin.

La decisión local quedó registrada en `808bce0`. La anotación en el issue o PR que acoja la excepción sigue pendiente según [CLAUDE.md](CLAUDE.md#mecanismo-de-registro-de-aprobaciones) y debe citar el régimen de excepciones de Ley VIII, Art. 14 y Anexo III. El registro formal requiere confirmar la identidad del aprobador, la vigencia y el control compensatorio conforme al Régimen Operativo de Excepciones.

## Procedencia e integridad

- Las [122 huellas históricas](evidencia/sha256-archivos.txt) se cotejaron con las entradas del ZIP original del laboratorio. Todas coincidieron. El [informe histórico](evidencia/auditoria.json) corresponde a ese ZIP.
- [MANIFEST.current.sha256](MANIFEST.current.sha256) registra el contenido integrado. Los enlaces simbólicos se verifican leyendo el contenido del descriptor canónico.
