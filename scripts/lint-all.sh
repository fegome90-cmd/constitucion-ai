#!/usr/bin/env bash
set -euo pipefail

echo "=== Running linters ==="

# Verificar que las herramientas existen
# Python tools via uv, shellcheck via system
for tool in ruff mypy bandit codespell; do
    if ! uv run "${tool}" --version >/dev/null 2>&1; then
        echo "❌ ${tool} no encontrado. Ejecuta: uv sync --group dev"
        exit 1
    fi
done

if ! command -v shellcheck >/dev/null 2>&1; then
    echo "❌ shellcheck no encontrado. Instala con: brew install shellcheck"
    exit 1
fi

echo "→ Codespell (Spelling)"
uv run codespell || true

echo "→ Ruff (Python)"
uv run ruff check . --fix
uv run ruff format .

echo "→ Mypy (Type checking)"
uv run mypy scripts/ --ignore-missing-imports || true

echo "→ Markdownlint"
uv run markdownlint-cli2 "**/*.md" --fix || true

echo "→ Yamllint"
uv run yamllint -c .yamllint.yaml . 2>/dev/null || true

echo "→ Shellcheck"
find . -name "*.sh" -exec shellcheck {} + || true

echo "→ Bandit (Security)"
uv run bandit -c pyproject.toml -r scripts/ || true

echo "=== All linters complete ==="
