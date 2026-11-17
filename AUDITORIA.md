# Auditoría de la integración · 17 de noviembre de 2026

## Dictamen: VALIDACIÓN PARCIAL

Los diez config kits y sus starters fueron integrados y **sus gates se ejecutaron de verdad en este entorno**, con los locks congelados y las versiones fijadas. No se certifica la evidence bar de todas las herramientas: hay excepciones documentadas más abajo.

## Gates ejecutados

| Kit | Comandos ejecutados | Resultado |
| --- | --- | --- |
| python | `uv sync --frozen`, ruff format/check, mypy src, pytest, uv build | PASS con ruff 0.17.5, mypy 2.4.1, pytest 9.2.0, uv 0.13.9 |
| typescript | `pnpm install --frozen-lockfile`, `pnpm run check` | PASS |
| react | idem | PASS |
| css | idem | PASS |
| playwright | idem + E2E con Chromium real | PASS (1 test Chromium) |
| puppeteer | idem + Chrome real | PASS (2 tests node:test) |
| rust | `rustup run 1.100.0 cargo` fmt/clippy/test/build --locked | PASS |
| go | `go test/vet/build ./...` con GOPROXY=off | PASS |
| java | `mvn package`, `mvn spotless:check`, `mvn test` | PASS (tras actualizar google-java-format a 2.0.0) |
| lua | Lua 5.4.9, stylua 2.6.0, busted 2.3.0 | PASS |

Suite del repo: 63 tests verdes. ruff, mypy, shellcheck y markdownlint sin hallazgos.

## Correcciones reales hechas durante la integración

- El ZIP nunca ejecutó Biome: TypeScript, React, Playwright y Puppeteer tenían errores de formato. Se corrigieron.
- `spotless:check` fallaba con google-java-format 1.30.0 bajo JDK 27; se fijó 2.0.0.
- El starter Python usaba pyrefly y rangos de versión; se alineó con mypy y pins exactos del config kit.
- El guard de pytest en `audit.py` y en el test del generador usaba `shutil.which` en vez de importabilidad del módulo: daba FAIL falso cuando el binario existe pero el módulo no.
- La toolchain Rust 1.100.0 no estaba instalada y el cargo de Nix (1.99.0) hacía shadowing: se instaló 1.100.0 y se invoca con `rustup run`.

## Advertencias y excepciones a la evidence bar

- **Lua**: busted (★1.649), StyLua (★2.340), LuaLS (★4.412) y LuaRocks (★3.753) no alcanzan ≥5k estrellas y no hay métrica de descargas verificable. Sus gates pasan, pero **no están certificados por la barra**. Requiere decisión del maintainer.
- **Java**: maven-compiler-plugin (★265) y maven-surefire-plugin (★466) están por debajo de la barra; se conservan por ser parte del build estándar de Maven. Maven Central no expone descargas.
- **Pins exactos detrás del latest**: `@types/node` 22.20.5 (alineado con Node 22), jsdom 27.0.0, Testing Library 16.3.0 y puppeteer 25.17.0. El verificador los reporta como AVISO, no como FAIL.
- **Playwright/Puppeteer**: los navegadores se instalaron y los E2E pasaron, pero no se versionan binarios de navegador: `setup` los descarga.

## Integridad

- `evidencia/sha256-archivos.txt` conserva la huella **inmutable del ZIP original** (sus rutas son `templates/...`, no `starters/...`).
- `MANIFEST.current.sha256` regresa el estado final del repo integrado.
- Orden de gobernanza: ADR-0004 y ADR-0005 se escribieron antes del código, y ADR-0002 quedó marcada como superseded.

## Cierre

Para pass completo: resolver la excepción de Lua (o aceptarla explícitamente) y volver a generar este informe desde los gates ejecutados.
