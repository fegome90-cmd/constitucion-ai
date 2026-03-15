#!/usr/bin/env bash
set -euo pipefail

echo "=== Running linters ==="

echo "→ Ruff (Python)"
ruff check . --fix
ruff format .

echo "→ Mypy (Type checking)"
mypy scripts/ --ignore-missing-imports || true

echo "→ Markdownlint"
markdownlint-cli2 "**/*.md" --fix || true

echo "→ Yamllint"
yamllint -c .yamllint.yaml . 2>/dev/null || true

echo "→ Shellcheck"
find . -name "*.sh" -exec shellcheck {} + || true

echo "=== All linters complete ==="
