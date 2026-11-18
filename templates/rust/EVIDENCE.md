# Evidencia de la evidence bar — kit rust

Relevamiento inicial del 17 de noviembre de 2026 (actualizado el 18 de noviembre de 2026). Barra: ≥1M descargas semanales o ≥5k estrellas, y actividad en los últimos seis meses. Un `NO PASA` no se oculta.

| Herramienta | Versión | Adopción | Actividad | Fuente | Estado |
| --- | --- | --- | --- | --- | --- |
| Toolchain Rust (`cargo`, `rustc`, `cargo test`) | 1.100.0 | ★122.209 (`rust-lang/rust`) | release 2026-11-12, commits `2026-11-18` | `channel-rust-stable.toml`, GitHub `rust-lang/rust` | PASA |
| `rustfmt` / `clippy` | componentes de 1.100.0 | ★122.209 (`rust-lang/rust`) | commits `2026-11-18` | `rust-toolchain.toml`, GitHub `rust-lang/rust` | PASA |

Toolchain `1.100.0` instalada explícitamente; se invoca anteponiendo `~/.cargo/bin` (o `rustup run 1.100.0 cargo`) para evitar el `cargo 1.99` de Nix que provoca shadowing en entornos locales. Gates ejecutados con `CARGO_NET_OFFLINE=true`.
