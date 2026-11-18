# Config kit: Rust

Kit mínimo y reproducible para proyectos Rust (Edition 2024, `rust-version = "1.85"`, toolchain fijado `1.100.0`). La capa ejecutable está en `starters/rust/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias / build | Cargo | 1.100.0 |
| Formatter | `rustfmt` (`cargo fmt`) | componente de 1.100.0 |
| Linter | `clippy` (`cargo clippy -D warnings`) | componente de 1.100.0 |
| Type-checker | `rustc` (compilador estático) | 1.100.0 |
| Test runner | `cargo test` | componente de 1.100.0 |

## Excluidos deliberadamente

- **`cargo-deny` / `cargo-audit` / `cargo-nextest`**: quedan fuera del mínimo base para no introducir herramientas externas fuera de `rustup` (`profile = "minimal"`); pueden sumarse por proyecto si se requiere auditoría de crates o runner paralelo.
- **`Cargo.lock` en el config kit**: el lockfile vive en `starters/rust/` (ADR-0004); en proyectos nuevos se genera al compilar y se versiona según política de binario o librería.

## Uso

Aplicar el kit a un directorio sin `Cargo.toml` ni `rust-toolchain.toml` previos con el script del repo:

```bash
scripts/apply-kit.sh rust <destino>
```

El script normaliza `name = "starter-rust"` a `name = "rust-config-kit-project"`, copia `Cargo.toml` y `rust-toolchain.toml`, omite `README.md` y `EVIDENCE.md`, y corre el smoke test offline (`cargo fmt`, `cargo clippy`, `cargo test`, `cargo build`). Para combinarlo con herramientas transversales, aplicar también `_common`.

Los detalles de adopción están en `EVIDENCE.md`.
