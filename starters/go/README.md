# Go · toolchain estándar

Sin dependencias externas. Go >=1.23; Go Modules, gofmt, go vet y go test.

```sh
go fmt ./...
go vet ./...
go test ./...
go build ./...
go run ./cmd/starter
```

`go.sum` aparece cuando hay dependencias que requieren checksums; un proyecto solo-stdlib no necesita inventarlo.

Control integrado: `go vet ./... && go test ./... && go build ./...`.
