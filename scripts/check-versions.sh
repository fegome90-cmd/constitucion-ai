#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: check-versions.sh [--registry-file <archivo.json>]" >&2
  echo "  Sin --registry-file consulta PyPI y npm registry en vivo." >&2
}

REGISTRY_FILE=""
while [[ $# -gt 0 ]]; do
  case "${1}" in
    --registry-file)
      REGISTRY_FILE="${2}"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"
TEMPLATES_DIR="${CONFIG_KITS_DIR:-${REPO_ROOT}/templates}"

authoritative_version() {
  local name="${1}"
  if [[ -n "${REGISTRY_FILE}" ]]; then
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' \
      "${REGISTRY_FILE}" "${name}"
  elif [[ "${name}" == "markdownlint-cli2" ]]; then
    curl -fsSL "https://registry.npmjs.org/${name}/latest" | jq -r '.version'
  else
    curl -fsSL "https://pypi.org/pypi/${name}/json" | jq -r '.info.version'
  fi
}

pinned=()

while IFS= read -r line; do
  if [[ "${line}" =~ \"([a-zA-Z0-9_-]+)==([0-9][0-9A-Za-z.\-]*)\" ]]; then
    pinned+=("${BASH_REMATCH[1]}|${BASH_REMATCH[2]}")
  fi
done < "${TEMPLATES_DIR}/python/pyproject.toml"

while IFS= read -r line; do
  if [[ "${line}" =~ ^([a-zA-Z0-9_-]+)==(.+)$ ]]; then
    pinned+=("${BASH_REMATCH[1]}|${BASH_REMATCH[2]}")
  fi
done < "${TEMPLATES_DIR}/_common/requirements-dev.txt"

npm_pin="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["devDependencies"]["markdownlint-cli2"])' \
  "${TEMPLATES_DIR}/_common/package.json")"
pinned+=("markdownlint-cli2|${npm_pin}")

drift=0

echo "=== Pins exactos ==="
inexact_report="$(python3 - "${TEMPLATES_DIR}" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
bad = []

pyproject = (root / "python/pyproject.toml").read_text()
for match in re.finditer(r'"([a-zA-Z0-9_-]+)\s*(>=|<=|~=|!=)\s*([^"\s]+)"', pyproject):
    bad.append(f"PIN NO EXACTO {match.group(1)}{match.group(2)}{match.group(3)}")

requirements = (root / "_common/requirements-dev.txt").read_text().splitlines()
for line in requirements:
    match = re.match(r"\s*([a-zA-Z0-9_-]+)\s*(>=|<=|~=|!=)\s*(\S+)", line)
    if match:
        bad.append(f"PIN NO EXACTO {match.group(1)}{match.group(2)}{match.group(3)}")

package = json.loads((root / "_common/package.json").read_text())
for name, spec in package.get("devDependencies", {}).items():
    if not re.fullmatch(r"\d+\.\d+\.\d+", spec):
        bad.append(f"PIN NO EXACTO {name}{spec}")

print("\n".join(bad))
PY
)"

if [[ -n "${inexact_report}" ]]; then
  echo "${inexact_report}"
  drift=1
else
  echo "OK: todos los pins son exactos"
fi

echo "=== Pins de config kits ==="
for entry in "${pinned[@]}"; do
  name="${entry%%|*}"
  pin="${entry#*|}"
  latest="$(authoritative_version "${name}")"
  if [[ -z "${latest}" ]]; then
    echo "SIN FUENTE ${name}: no se pudo resolver versión autoritativa"
    drift=1
  elif [[ "${pin}" != "${latest}" ]]; then
    echo "DRIFT ${name}: pin ${pin}, vigente ${latest}"
    drift=1
  else
    echo "OK ${name}: ${pin}"
  fi
done

echo "=== pre-commit vs lockfile ==="
echo "Nota: los pins del kit se resuelven desde el registry; los revs de pre-commit se alinean con uv.lock."
echo "Fuentes distintas por decisión: pueden diferir sin ser drift."
precommit_report="$(python3 - "${REPO_ROOT}" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
lock = (root / "uv.lock").read_text()
versions = dict(re.findall(r'name = "([^"]+)"\nversion = "([^"]+)"', lock))

mapping = {
    "https://github.com/codespell-project/codespell": "codespell",
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
    "https://github.com/PyCQA/bandit": "bandit",
}

lines = (root / ".pre-commit-config.yaml").read_text().splitlines()
for i, line in enumerate(lines):
    if not line.strip().startswith("- repo:"):
        continue
    url = line.split("repo:", 1)[1].strip()
    package = mapping.get(url)
    if not package:
        continue
    rev = None
    for following in lines[i + 1 : i + 4]:
        match = re.match(r"\s*rev:\s*(\S+)", following)
        if match:
            rev = match.group(1)
            break
    if rev and package in versions and rev.lstrip("v") != versions[package]:
        print(f"PRE-COMMIT DRIFT {package}: rev {rev}, lock {versions[package]}")
PY
)"

if [[ -n "${precommit_report}" ]]; then
  echo "${precommit_report}"
  drift=1
else
  echo "OK: revs de pre-commit alineados con el lockfile"
fi

exit "${drift}"
