# Rust · Cargo + rustfmt + Clippy

Rust 2024 Edition, toolchain 1.100.0 fijado para el ejemplo. Los tests no usan dependencias externas.

```sh
rustup toolchain install 1.100.0 --component clippy --component rustfmt
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test --locked
cargo build --locked
cargo run --locked
```

`Cargo.lock` está versionado para reproducibilidad. Para nuevas librerías redistribuidas, decidir explícitamente la política de lockfile.

Control integrado: `cargo fmt --all -- --check && cargo clippy --all-targets -- -D warnings && cargo test --locked && cargo build --locked`.
