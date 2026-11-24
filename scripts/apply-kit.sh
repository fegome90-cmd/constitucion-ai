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
FILES=()
while IFS= read -r file; do
  FILES+=("${file}")
done < <(find "${KIT_DIR}" -maxdepth 1 -type f ! -name README.md ! -name EVIDENCE.md -exec basename {} \; | sort)

for file in "${FILES[@]}"; do
  if [[ -e "${DEST}/${file}" ]]; then
    echo "ERROR: el destino ya contiene '${file}'. No se sobrescribe configuración existente." >&2
    exit 1
  fi
done

for file in "${FILES[@]}"; do
  if [[ "${KIT}" == "python" && "${file}" == "pyproject.toml" ]]; then
    # Target projects without an existing pyproject.toml receive tool config and a generic descriptor.
    awk '
      /^\[[^]]+\]/ {
        s = $0
        sub(/[[:space:]]*(#.*)?$/, "", s)
        section = s
      }
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
  elif [[ "${KIT}" == "go" && "${file}" == "go.mod" ]]; then
    sed 's|^module example\.com/starter-go$|module example.com/go-config-kit-project|' \
      "${KIT_DIR}/${file}" > "${DEST}/${file}"
  elif [[ "${KIT}" == "java" && "${file}" == "pom.xml" ]]; then
    sed 's|<artifactId>starter-java</artifactId>|<artifactId>java-config-kit-project</artifactId>|' \
      "${KIT_DIR}/${file}" > "${DEST}/${file}"
  elif [[ "${KIT}" == "rust" && "${file}" == "Cargo.toml" ]]; then
    sed 's/^name = "starter-rust"$/name = "rust-config-kit-project"/' \
      "${KIT_DIR}/${file}" > "${DEST}/${file}"
  elif [[ "${file}" == "package.json" && "${KIT}" != "_common" ]]; then
    sed "s/\"name\": \"starter-${KIT}\"/\"name\": \"${KIT}-config-kit-project\"/" \
      "${KIT_DIR}/${file}" > "${DEST}/${file}"
  else
    cp "${KIT_DIR}/${file}" "${DEST}/${file}"
  fi
done

echo "Kit '${KIT}' aplicado en ${DEST}"

smoke_python() {
  local starter_bin="${REPO_ROOT}/starters/python/.venv/bin"
  local smoke_path="${PATH}"
  if [[ -x "${starter_bin}/ruff" && -x "${starter_bin}/mypy" && -x "${starter_bin}/pytest" ]]; then
    smoke_path="${starter_bin}:${PATH}"
  elif ! command -v ruff >/dev/null 2>&1 || ! command -v mypy >/dev/null 2>&1 || ! command -v pytest >/dev/null 2>&1; then
    echo "Smoke test Python: omitido (faltan ruff/mypy/pytest o starters/python/.venv)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/pyproject.toml" "${fixture}/pyproject.toml"
  mkdir -p "${fixture}/src" "${fixture}/tests"
  printf 'def add(a: int, b: int) -> int:\n    return a + b\n' > "${fixture}/src/example.py"
  printf 'from example import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) == 3\n' > "${fixture}/tests/test_example.py"

  echo "Smoke test Python: ruff format --check"
  (cd "${fixture}" && PATH="${smoke_path}" ruff format --check .)
  echo "Smoke test Python: ruff check"
  (cd "${fixture}" && PATH="${smoke_path}" ruff check .)
  echo "Smoke test Python: mypy"
  (cd "${fixture}" && PATH="${smoke_path}" mypy src)
  echo "Smoke test Python: pytest"
  (cd "${fixture}" && PATH="${smoke_path}" pytest -q)
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

smoke_go() {
  if ! command -v go >/dev/null 2>&1 || ! command -v gofmt >/dev/null 2>&1; then
    echo "Smoke test Go: omitido (falta go o gofmt)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/go.mod" "${fixture}/go.mod"
  mkdir -p "${fixture}/cmd/example" "${fixture}/greet"
  printf 'package greet\n\nfunc Add(a, b int) int {\n\treturn a + b\n}\n' > "${fixture}/greet/greet.go"
  printf 'package greet\n\nimport "testing"\n\nfunc TestAdd(t *testing.T) {\n\tif Add(1, 2) != 3 {\n\t\tt.Fatal("expected 3")\n\t}\n}\n' > "${fixture}/greet/greet_test.go"
  printf 'package main\n\nimport (\n\t"fmt"\n\n\t"example.com/go-config-kit-project/greet"\n)\n\nfunc main() {\n\tfmt.Println(greet.Add(1, 2))\n}\n' > "${fixture}/cmd/example/main.go"

  echo "Smoke test Go: gofmt"
  local unformatted
  unformatted="$(cd "${fixture}" && gofmt -l .)"
  if [[ -n "${unformatted}" ]]; then
    echo "ERROR: archivos sin formato Go: ${unformatted}" >&2
    return 1
  fi
  echo "Smoke test Go: go vet"
  (cd "${fixture}" && GOPROXY=off GOWORK=off GOTOOLCHAIN=local go vet ./...)
  echo "Smoke test Go: go test"
  (cd "${fixture}" && GOPROXY=off GOWORK=off GOTOOLCHAIN=local go test ./...)
  echo "Smoke test Go: go build"
  (cd "${fixture}" && GOPROXY=off GOWORK=off GOTOOLCHAIN=local go build ./...)
}

smoke_java() {
  if ! command -v mvn >/dev/null 2>&1 || ! command -v java >/dev/null 2>&1; then
    echo "Smoke test Java: omitido (falta mvn o java)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/pom.xml" "${fixture}/pom.xml"
  mkdir -p "${fixture}/src/main/java/org/example/kit" "${fixture}/src/test/java/org/example/kit"
  printf 'package org.example.kit;\n\npublic final class App {\n  private App() {}\n\n  public static int add(int a, int b) {\n    return a + b;\n  }\n}\n' > "${fixture}/src/main/java/org/example/kit/App.java"
  printf 'package org.example.kit;\n\nimport static org.junit.jupiter.api.Assertions.assertEquals;\n\nimport org.junit.jupiter.api.Test;\n\nclass AppTest {\n  @Test\n  void adds() {\n    assertEquals(3, App.add(1, 2));\n  }\n}\n' > "${fixture}/src/test/java/org/example/kit/AppTest.java"

  echo "Smoke test Java: spotless:check verify"
  (cd "${fixture}" && mvn -q spotless:check verify)
}

smoke_rust() {
  local smoke_path="${PATH}"
  if [[ -x "${HOME}/.cargo/bin/cargo" && -x "${HOME}/.cargo/bin/rustc" ]]; then
    smoke_path="${HOME}/.cargo/bin:${PATH}"
  elif ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
    echo "Smoke test Rust: omitido (falta cargo o rustc)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/Cargo.toml" "${DEST}/rust-toolchain.toml" "${fixture}/"
  mkdir -p "${fixture}/src"
  printf 'pub fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n\n#[cfg(test)]\nmod tests {\n    use super::add;\n\n    #[test]\n    fn adds() {\n        assert_eq!(add(1, 2), 3);\n    }\n}\n' > "${fixture}/src/lib.rs"
  printf 'fn main() {\n    println!("{}", rust_config_kit_project::add(1, 2));\n}\n' > "${fixture}/src/main.rs"

  echo "Smoke test Rust: cargo fmt --check"
  (cd "${fixture}" && PATH="${smoke_path}" CARGO_NET_OFFLINE=true cargo fmt --all -- --check)
  echo "Smoke test Rust: cargo clippy"
  (cd "${fixture}" && PATH="${smoke_path}" CARGO_NET_OFFLINE=true cargo clippy --all-targets -- -D warnings)
  echo "Smoke test Rust: cargo test"
  (cd "${fixture}" && PATH="${smoke_path}" CARGO_NET_OFFLINE=true cargo test --offline)
  echo "Smoke test Rust: cargo build"
  (cd "${fixture}" && PATH="${smoke_path}" CARGO_NET_OFFLINE=true cargo build --offline)
}

smoke_css() {
  local starter_nm="${REPO_ROOT}/starters/css/node_modules"
  if [[ ! -d "${starter_nm}" ]]; then
    echo "Smoke test CSS: omitido (falta starters/css/node_modules)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/package.json" "${DEST}/biome.json" "${fixture}/"
  ln -s "${starter_nm}" "${fixture}/node_modules"
  mkdir -p "${fixture}/src" "${fixture}/tests"
  printf '<!doctype html>\n<html lang="es">\n  <head>\n    <meta charset="UTF-8" />\n    <title>css-config-kit-project</title>\n    <link rel="stylesheet" href="/src/styles.css" />\n  </head>\n  <body>\n    <main class="card">OK</main>\n  </body>\n</html>\n' > "${fixture}/index.html"
  printf '@layer tokens {\n  :root {\n    --surface: #f6f4ef;\n  }\n}\n\n.card {\n  background: var(--surface);\n}\n' > "${fixture}/src/styles.css"
  printf 'import assert from "node:assert/strict";\nimport { readFileSync } from "node:fs";\nimport test from "node:test";\n\ntest("css tokens", () => {\n  const css = readFileSync(\n    new URL("../src/styles.css", import.meta.url),\n    "utf8",\n  );\n  assert.match(css, /@layer tokens/);\n});\n' > "${fixture}/tests/styles.test.mjs"

  echo "Smoke test CSS: biome check"
  (cd "${fixture}" && ./node_modules/.bin/biome check src/ tests/)
  echo "Smoke test CSS: node --test"
  (cd "${fixture}" && node --test tests/*.test.mjs)
  echo "Smoke test CSS: vite build"
  (cd "${fixture}" && ./node_modules/.bin/vite build)
}

smoke_playwright() {
  local starter_nm="${REPO_ROOT}/starters/playwright/node_modules"
  if [[ ! -d "${starter_nm}" ]]; then
    echo "Smoke test Playwright: omitido (falta starters/playwright/node_modules)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/package.json" "${DEST}/biome.json" "${DEST}/playwright.config.ts" "${DEST}/tsconfig.json" "${fixture}/"
  ln -s "${starter_nm}" "${fixture}/node_modules"
  mkdir -p "${fixture}/fixtures" "${fixture}/src" "${fixture}/tests"
  printf '<!doctype html>\n<html lang="es">\n  <head><meta charset="UTF-8" /><title>Contador</title></head>\n  <body>\n    <output id="count">0</output>\n    <button type="button" id="inc">Incrementar</button>\n    <script>\n      const c = document.querySelector("#count");\n      document.querySelector("#inc").addEventListener("click", () => {\n        c.textContent = String(Number(c.textContent) + 1);\n      });\n    </script>\n  </body>\n</html>\n' > "${fixture}/fixtures/index.html"
  printf 'import { readFileSync } from "node:fs";\nimport { createServer } from "node:http";\n\nconst fixture = readFileSync(\n  new URL("../fixtures/index.html", import.meta.url),\n);\nconst port = Number(process.env.PORT ?? "4173");\ncreateServer((_, res) => {\n  res\n    .writeHead(200, { "Content-Type": "text/html; charset=utf-8" })\n    .end(fixture);\n}).listen(port, "127.0.0.1");\n' > "${fixture}/src/server.mjs"
  printf 'import { expect, test } from "@playwright/test";\n\ntest("incrementa contador", async ({ page }) => {\n  await page.goto("/");\n  await expect(page.getByRole("status")).toHaveText("0");\n  await page.getByRole("button", { name: "Incrementar" }).click();\n  await expect(page.getByRole("status")).toHaveText("1");\n});\n' > "${fixture}/tests/counter.spec.ts"

  echo "Smoke test Playwright: biome check"
  (cd "${fixture}" && ./node_modules/.bin/biome check .)
  echo "Smoke test Playwright: tsc --noEmit"
  (cd "${fixture}" && ./node_modules/.bin/tsc --noEmit)

  local has_chromium
  has_chromium="$(cd "${fixture}" && node --input-type=module -e 'import { chromium } from "@playwright/test"; import { existsSync } from "node:fs"; process.stdout.write(existsSync(chromium.executablePath()) ? "1" : "0");' 2>/dev/null || printf '0')"
  if [[ "${has_chromium}" != "1" ]]; then
    echo "Smoke test Playwright: playwright test omitido (falta binario Chromium)."
    return 0
  fi

  local smoke_port
  smoke_port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
  echo "Smoke test Playwright: playwright test"
  (cd "${fixture}" && CI=true PLAYWRIGHT_HTML_OPEN=never PORT="${smoke_port}" ./node_modules/.bin/playwright test)
}

smoke_puppeteer() {
  local starter_nm="${REPO_ROOT}/starters/puppeteer/node_modules"
  if [[ ! -d "${starter_nm}" ]]; then
    echo "Smoke test Puppeteer: omitido (falta starters/puppeteer/node_modules)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/package.json" "${DEST}/biome.json" "${DEST}/tsconfig.json" "${DEST}/tsconfig.build.json" "${fixture}/"
  ln -s "${starter_nm}" "${fixture}/node_modules"
  mkdir -p "${fixture}/src" "${fixture}/tests"
  printf 'export function title(label: string): string {\n  const trimmed = label.trim();\n  if (!trimmed) throw new Error("Falta el título");\n  return trimmed;\n}\n' > "${fixture}/src/utils.ts"
  cat <<'EOF' > "${fixture}/src/main.ts"
import puppeteer from "puppeteer";
import { title } from "./utils.js";

async function main(): Promise<void> {
  const browser = await puppeteer.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.setContent("<h1>Automatización lista</h1>");
    const heading = await page.$eval(
      "h1",
      (el) => el.textContent?.trim() ?? "",
    );
    console.log(title(heading));
  } finally {
    await browser.close();
  }
}

await main();
EOF
  printf 'import assert from "node:assert/strict";\nimport test from "node:test";\nimport { title } from "../src/utils.js";\n\ntest("normaliza título", () => {\n  assert.equal(title(" demo "), "demo");\n});\n\ntest("rechaza título vacío", () => {\n  assert.throws(() => title("   "));\n});\n' > "${fixture}/tests/utils.test.ts"

  echo "Smoke test Puppeteer: biome check"
  (cd "${fixture}" && ./node_modules/.bin/biome check .)
  echo "Smoke test Puppeteer: tsc --noEmit"
  (cd "${fixture}" && ./node_modules/.bin/tsc --noEmit)
  echo "Smoke test Puppeteer: tsx --test"
  (cd "${fixture}" && ./node_modules/.bin/tsx --test tests/*.test.ts)
  echo "Smoke test Puppeteer: build"
  (cd "${fixture}" && ./node_modules/.bin/tsc -p tsconfig.build.json)

  local has_chrome
  has_chrome="$(cd "${fixture}" && node --input-type=module -e 'import puppeteer from "puppeteer"; import { existsSync } from "node:fs"; process.stdout.write(existsSync(await puppeteer.executablePath()) ? "1" : "0");' 2>/dev/null || printf '0')"
  if [[ "${has_chrome}" != "1" ]]; then
    echo "Smoke test Puppeteer: node dist/main.js omitido (falta binario Chrome)."
    return 0
  fi

  echo "Smoke test Puppeteer: node dist/main.js"
  (cd "${fixture}" && node dist/main.js)
}

smoke_lua() {
  local smoke_path="${PATH}"
  if [[ -d "${HOME}/.luarocks/bin" ]]; then
    smoke_path="${HOME}/.luarocks/bin:${smoke_path}"
  fi
  if [[ -d "/opt/homebrew/opt/lua@5.4/bin" ]]; then
    smoke_path="/opt/homebrew/opt/lua@5.4/bin:${smoke_path}"
  fi

  if ! PATH="${smoke_path}" command -v lua >/dev/null 2>&1 \
    || ! PATH="${smoke_path}" command -v stylua >/dev/null 2>&1 \
    || ! PATH="${smoke_path}" command -v busted >/dev/null 2>&1; then
    echo "Smoke test Lua: omitido (faltan lua/stylua/busted)."
    return 0
  fi

  local fixture
  fixture="$(mktemp -d)"
  trap 'rm -rf "${fixture}"' RETURN

  cp "${DEST}/rocks.txt" "${DEST}/.stylua.toml" "${DEST}/.luarc.json" "${fixture}/"
  mkdir -p "${fixture}/src" "${fixture}/spec"
  printf 'local M = {}\n\nfunction M.greet(name)\n  assert(type(name) == "string", "name debe ser un string")\n  local clean = name:match("^%%s*(.-)%%s*$")\n  if clean == "" then\n    return "Hola, desconocido"\n  end\n  return "Hola, " .. clean\nend\n\nreturn M\n' > "${fixture}/src/starter.lua"
  printf 'package.path = "src/?.lua;" .. package.path\n\nlocal starter = require("starter")\nprint(starter.greet("Lua"))\n' > "${fixture}/src/main.lua"
  printf 'package.path = "src/?.lua;" .. package.path\n\nlocal starter = require("starter")\n\ndescribe("starter.greet", function()\n  it("saluda", function()\n    assert.are.equal("Hola, Lua", starter.greet(" Lua "))\n  end)\nend)\n' > "${fixture}/spec/starter_spec.lua"

  echo "Smoke test Lua: stylua --check"
  (cd "${fixture}" && PATH="${smoke_path}" stylua --check src spec)
  echo "Smoke test Lua: busted"
  (cd "${fixture}" && PATH="${smoke_path}" busted)
  echo "Smoke test Lua: lua src/main.lua"
  (cd "${fixture}" && PATH="${smoke_path}" lua src/main.lua)
}

case "${KIT}" in
  css) smoke_css ;;
  go) smoke_go ;;
  java) smoke_java ;;
  lua) smoke_lua ;;
  playwright) smoke_playwright ;;
  puppeteer) smoke_puppeteer ;;
  python) smoke_python ;;
  rust) smoke_rust ;;
  typescript) smoke_typescript ;;
  react) smoke_react ;;
  *) echo "Kit '${KIT}' aplicado; no tiene smoke test ejecutable." ;;
esac
