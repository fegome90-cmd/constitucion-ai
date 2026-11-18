#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: apply-kit.sh <kit> <destino>" >&2
  echo "  kit: css | go | java | lua | playwright | puppeteer | python | react | rust | typescript | _common" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

KIT="${1}"
DEST="${2}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"
TEMPLATES="${REPO_ROOT}/templates"
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
  if [[ "${KIT}" == "python" && "${file}" == "pyproject.toml" ]]; then
    # Existing projects receive the tool configuration and the generic project descriptor.
    awk '
      /^\[/ { section = $0 }
      section == "[build-system]" { next }
      section == "[project]" && /^readme[[:space:]]*=/ { next }
      section == "[project]" && /^name[[:space:]]*=/ {
        $0 = "name = \"python-config-kit-project\""
      }
      section == "[project]" && /^description[[:space:]]*=/ {
        $0 = "description = \"Proyecto mínimo generado desde el config kit Python\""
      }
      { print }
    ' "${KIT_DIR}/${file}" > "${DEST}/${file}"
  elif [[ "${file}" == "package.json" && "${KIT}" != "_common" ]]; then
    sed "s/\"name\": \"starter-${KIT}\"/\"name\": \"${KIT}-config-kit-project\"/" \
      "${KIT_DIR}/${file}" > "${DEST}/${file}"
  else
    cp "${KIT_DIR}/${file}" "${DEST}/${file}"
  fi
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

smoke_typescript() {
  local starter_nm="${REPO_ROOT}/starters/typescript/node_modules"
  if [[ ! -d "${starter_nm}" ]]; then
    echo "Smoke test TypeScript: omitido (falta starters/typescript/node_modules)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/package.json" "${DEST}/biome.json" "${DEST}/tsconfig.json" "${DEST}/tsconfig.build.json" "${fixture}/"
  ln -s "${starter_nm}" "${fixture}/node_modules"
  mkdir -p "${fixture}/src" "${fixture}/tests"
  printf 'export function add(a: number, b: number): number {\n  return a + b;\n}\n' > "${fixture}/src/index.ts"
  printf 'import { describe, expect, it } from "vitest";\nimport { add } from "../src/index.js";\n\ndescribe("add", () => {\n  it("suma", () => {\n    expect(add(1, 2)).toBe(3);\n  });\n});\n' > "${fixture}/tests/index.test.ts"

  echo "Smoke test TypeScript: biome check"
  (cd "${fixture}" && ./node_modules/.bin/biome check .)
  echo "Smoke test TypeScript: tsc --noEmit"
  (cd "${fixture}" && ./node_modules/.bin/tsc --noEmit)
  echo "Smoke test TypeScript: vitest run"
  (cd "${fixture}" && ./node_modules/.bin/vitest run)
  echo "Smoke test TypeScript: build"
  (cd "${fixture}" && ./node_modules/.bin/tsc -p tsconfig.build.json)
}

smoke_react() {
  local starter_nm="${REPO_ROOT}/starters/react/node_modules"
  if [[ ! -d "${starter_nm}" ]]; then
    echo "Smoke test React: omitido (falta starters/react/node_modules)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/package.json" "${DEST}/biome.json" "${DEST}/tsconfig.json" "${DEST}/vite.config.ts" "${DEST}/vitest.config.ts" "${fixture}/"
  ln -s "${starter_nm}" "${fixture}/node_modules"
  mkdir -p "${fixture}/src"
  printf '<!doctype html>\n<html lang="es">\n  <head>\n    <meta charset="UTF-8" />\n    <title>react-config-kit-project</title>\n  </head>\n  <body>\n    <div id="root"></div>\n    <script type="module" src="/src/main.tsx"></script>\n  </body>\n</html>\n' > "${fixture}/index.html"
  printf 'export function App() {\n  return <button type="button">OK</button>;\n}\n' > "${fixture}/src/App.tsx"
  printf 'import { StrictMode } from "react";\nimport { createRoot } from "react-dom/client";\nimport { App } from "./App";\n\nconst root = document.getElementById("root");\nif (root) {\n  createRoot(root).render(\n    <StrictMode>\n      <App />\n    </StrictMode>,\n  );\n}\n' > "${fixture}/src/main.tsx"
  printf 'import { render, screen } from "@testing-library/react";\nimport { describe, expect, it } from "vitest";\nimport { App } from "./App";\n\ndescribe("App", () => {\n  it("renderiza", () => {\n    render(<App />);\n    expect(screen.getByRole("button", { name: "OK" })).toBeTruthy();\n  });\n});\n' > "${fixture}/src/App.test.tsx"

  echo "Smoke test React: biome check"
  (cd "${fixture}" && ./node_modules/.bin/biome check .)
  echo "Smoke test React: tsc --noEmit"
  (cd "${fixture}" && ./node_modules/.bin/tsc --noEmit)
  echo "Smoke test React: vitest run"
  (cd "${fixture}" && ./node_modules/.bin/vitest run)
  echo "Smoke test React: vite build"
  (cd "${fixture}" && ./node_modules/.bin/vite build)
}

case "${KIT}" in
  python) smoke_python ;;
  typescript) smoke_typescript ;;
  react) smoke_react ;;
  *) echo "Kit '${KIT}' aplicado; no tiene smoke test ejecutable." ;;
esac
