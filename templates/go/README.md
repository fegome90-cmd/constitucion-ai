# Config kit: Go

Kit mínimo y reproducible para proyectos Go (`>=1.23`) sin dependencias externas. La capa ejecutable está en `starters/go/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias | Go Modules (`go mod`) | 1.23 |
| Formatter | `gofmt` / `go fmt` | componente de Go |
| Linter | `go vet` | componente de Go |
| Type-checker | Compilador Go (`go build`) | estático integrado |
| Test runner | `go test` | componente de Go |

## Excluidos deliberadamente

- **golangci-lint / staticcheck**: quedan fuera del núcleo mínimo para evitar dependencias externas fuera del toolchain estándar; pueden agregarse por proyecto si se necesita análisis estático adicional.
- **`go.sum` vacío**: Go Modules solo genera `go.sum` cuando el módulo declara dependencias externas con checksums.

## Uso

Aplicar el kit a un directorio sin `go.mod` previo con el script del repo:

```bash
scripts/apply-kit.sh go <destino>
```

El script normaliza `module example.com/starter-go` a `module example.com/go-config-kit-project`, conserva `go 1.23`, omite `README.md` y `EVIDENCE.md`, y corre el smoke test offline. Para combinarlo con herramientas transversales, aplicar también `_common`.

Los detalles de adopción y la nota sobre `go 1.23` están en `EVIDENCE.md`.
