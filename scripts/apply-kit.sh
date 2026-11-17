#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: apply-kit.sh <kit> <destino>" >&2
  echo "  kit: python | _common" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

KIT="${1}"
DEST="${2}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$(dirname "${SCRIPT_DIR}")/templates"
KIT_DIR="${TEMPLATES}/${KIT}"

if [[ ! -d "${KIT_DIR}" ]]; then
  echo "ERROR: no existe el config kit '${KIT}' en ${TEMPLATES}" >&2
  exit 2
fi

if [[ ! -d "${DEST}" ]]; then
  echo "ERROR: el destino no existe o no es un directorio: ${DEST}" >&2
  exit 2
fi

# Los docs del kit no son archivos de configuración del proyecto destino.
mapfile -t FILES < <(find "${KIT_DIR}" -maxdepth 1 -type f ! -name README.md ! -name EVIDENCE.md -exec basename {} \; | sort)

for file in "${FILES[@]}"; do
  if [[ -e "${DEST}/${file}" ]]; then
    echo "ERROR: el destino ya contiene '${file}'. No se sobrescribe configuración existente." >&2
    exit 1
  fi
done

for file in "${FILES[@]}"; do
  cp "${KIT_DIR}/${file}" "${DEST}/${file}"
done

echo "Kit '${KIT}' aplicado en ${DEST}"

smoke_python() {
  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/pyproject.toml" "${fixture}/pyproject.toml"
  mkdir -p "${fixture}/src" "${fixture}/tests"
  printf 'def add(a: int, b: int) -> int:\n    return a + b\n' > "${fixture}/src/example.py"
  printf 'from example import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) == 3\n' > "${fixture}/tests/test_example.py"

  echo "Smoke test Python: ruff check"
  (cd "${fixture}" && ruff check .)
  echo "Smoke test Python: mypy"
  (cd "${fixture}" && mypy src)
  echo "Smoke test Python: pytest"
  (cd "${fixture}" && pytest -q)
}

case "${KIT}" in
  python) smoke_python ;;
  *) echo "Kit '${KIT}' aplicado; no tiene smoke test ejecutable." ;;
esac
