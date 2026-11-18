# Evidencia de la evidence bar — kit go

Relevamiento inicial del 17 de noviembre de 2026 (actualizado el 18 de noviembre de 2026). Barra: ≥1M descargas semanales o ≥5k estrellas, y actividad en los últimos seis meses. Un `NO PASA` no se oculta.

| Herramienta | Versión | Adopción | Actividad | Fuente | Estado |
| --- | --- | --- | --- | --- | --- |
| Toolchain Go (`go`, `go mod`, `go build`) | 1.23 | ★140.061 (`golang/go`) | release 1.27.4 (`2026-11-02`), commits `2026-11-18` | `go.dev/VERSION`, GitHub `golang/go` | PASA |
| `gofmt` / `go vet` / `go test` | componentes del toolchain | ★140.061 (`golang/go`) | commits `2026-11-18` | GitHub `golang/go` | PASA |

Sin dependencias externas; gates ejecutados con `GOPROXY=off`, `GOWORK=off` y `GOTOOLCHAIN=local`.

`go.mod` fija la directiva de compatibilidad `go 1.23` (`Go >=1.23` en `catalog.json` y `starter.json`) para ejecutarse sin descargas automáticas de toolchain en entornos locales (p. ej. `go1.27.3`), mientras `go.dev/VERSION` reporta `1.27.4`; ese `DRIFT` queda visible en `scripts/check-versions.sh` sin romper `GOTOOLCHAIN=local`.
