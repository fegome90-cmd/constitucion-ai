#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"

exec python3 - "${REPO_ROOT}" "$@" <<'PY'
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

root = pathlib.Path(sys.argv[1])
args = sys.argv[2:]
registry_file = None
while args:
    flag = args.pop(0)
    if flag == "--registry-file" and args:
        registry_file = pathlib.Path(args.pop(0))
    elif flag == "--root" and args:
        root = pathlib.Path(args.pop(0))
    else:
        print("Uso: check-versions.sh [--root <dir>] [--registry-file <archivo.json>]", file=sys.stderr)
        raise SystemExit(2)

offline = json.loads(registry_file.read_text()) if registry_file else {}
catalog = json.loads((root / "catalog.json").read_text())

def pep440_pins(text):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "[dependency-groups]"), None)
    if start is None:
        return {}
    block = []
    for line in lines[start + 1 :]:
        if line.startswith("["):
            break
        block.append(line)
    return dict(re.findall(r'"([a-zA-Z0-9_.-]+)==([^"\s]+)"', "\n".join(block)))


PARSERS = {
    "pep440-exact": pep440_pins,
    "npm-exact": lambda text: {
        name: spec
        for name, spec in {
            **json.loads(text).get("dependencies", {}),
            **json.loads(text).get("devDependencies", {}),
        }.items()
        if re.fullmatch(r"\d+\.\d+\.\d+", spec)
    },
    "luarocks-exact": lambda text: dict(re.findall(r"^([a-zA-Z0-9_-]+)==(\S+)$", text, re.M)),
    "maven-properties": lambda text: {
        m.group(1): m.group(2)
        for m in re.finditer(r"<([a-zA-Z.-]+)\.version>([^<]+)</\1\.version>", text)
    },
    "rustup-channel": lambda text: {"rust": m.group(1)} if (m := re.search(r'channel\s*=\s*"([^"]+)"', text)) else {},
    "gomod-version": lambda text: {"go": re.search(r"^go\s+(\S+)", text, re.M).group(1)} if re.search(r"^go\s+(\S+)", text, re.M) else {},
}

REGISTRY_URLS = {
    "pypi": lambda n: f"https://pypi.org/pypi/{n}/json",
    "npm": lambda n: f"https://registry.npmjs.org/{n}/latest",
    "maven": lambda n: f"https://repo1.maven.org/maven2/{n.replace(':', '/')}/maven-metadata.xml",
    "rustup": lambda n: f"https://static.rust-lang.org/dist/channel-rust-{n}.toml",
    "go": lambda n: "https://go.dev/VERSION?m=text",
    "luarocks": lambda n: f"https://api.github.com/repos/{n}/releases/latest",
}

MAVEN_ARTIFACTS = {
    "junit": "org/junit/jupiter/junit-jupiter",
    "spotless": "com/diffplug/spotless/spotless-maven-plugin",
    "google-java-format": "com/google/googlejavaformat/google-java-format",
    "compiler": "org/apache/maven/plugins/maven-compiler-plugin",
    "surefire": "org/apache/maven/plugins/maven-surefire-plugin",
}
LUA_REPOS = {
    "busted": "lunarmodules/busted",
    "stylua": "JohnnyMorganz/StyLua",
}


def resolve(registry, name, version):
    if registry_file is not None:
        return offline.get(name, "")
    lookup = version if registry in ("rustup", "go") else name
    try:
        url = REGISTRY_URLS[registry](MAVEN_ARTIFACTS.get(name, name) if registry == "maven" else LUA_REPOS.get(name, name) if registry == "luarocks" else lookup)
        req = urllib.request.Request(url, headers={"User-Agent": "config-kits-check/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read().decode()
        if registry == "pypi":
            return json.loads(body)["info"]["version"]
        if registry == "npm":
            return json.loads(body)["version"]
        if registry == "maven":
            meta = ET.fromstring(body)
            return meta.findtext("./versioning/release") or meta.findtext("./versioning/latest") or ""
        if registry == "rustup":
            return version if response.status == 200 else ""
        if registry == "go":
            return body.splitlines()[0].removeprefix("go")
        if registry == "luarocks":
            try:
                return json.loads(body).get("tag_name", "").lstrip("v")
            except Exception:
                # Sin API (rate limit): verificamos que el tag exista por HTTP y devolvemos el pin.
                repo = LUA_REPOS.get(name, name)
                tag = urllib.request.Request(
                    f"https://github.com/{repo}/releases/tag/v{version}",
                    method="HEAD",
                    headers={"User-Agent": "config-kits-check/1.0"},
                )
                with urllib.request.urlopen(tag, timeout=15) as response:
                    return version if response.status == 200 else ""
    except Exception:
        if registry == "luarocks":
            # Sin API (rate limit): verificamos el tag por HTTP, sin consultar "latest".
            repo = LUA_REPOS.get(name, name)
            try:
                req = urllib.request.Request(
                    f"https://github.com/{repo}/releases/tag/v{version}",
                    method="HEAD",
                    headers={"User-Agent": "config-kits-check/1.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    return version if response.status == 200 else ""
            except Exception:
                return ""
        return ""
    return ""


drift = 0
print("=== Pins por catálogo ===")
for entry in catalog["templates"]:
    pins = entry["pins"]
    parser = PARSERS.get(pins["format"])
    registry = pins["registry"]
    if parser is None or registry not in REGISTRY_URLS:
        print(f"SIN FUENTE {entry['id']}: formato '{pins['format']}' o registry '{registry}' desconocido")
        drift = 1
        continue
    path = root / entry["config_dir"] / pins["file"]
    if not path.is_file():
        print(f"SIN FUENTE {entry['id']}: falta {path.relative_to(root)}")
        drift = 1
        continue
    text = path.read_text()
    found = parser(text)
    if pins["format"] in ("pep440-exact", "luarocks-exact"):
        for match in re.finditer(r'([a-zA-Z0-9_.-]+)\s*(>=|<=|~=|!=)\s*([^"\s,]+)', text):
            print(f"PIN NO EXACTO {entry['id']}/{match.group(1)}{match.group(2)}{match.group(3)}")
            drift = 1
    if pins["format"] == "npm-exact":
        data = json.loads(text)
        for name, spec in {**data.get("dependencies", {}), **data.get("devDependencies", {})}.items():
            if not re.fullmatch(r"\d+\.\d+\.\d+", spec):
                print(f"PIN NO EXACTO {entry['id']}/{name}{spec}")
                drift = 1
    if not found:
        print(f"SIN FUENTE {entry['id']}: no se pudieron extraer pins de {pins['file']}")
        drift = 1
        continue
    for name, pinned in found.items():
        latest = resolve(registry, name, pinned)
        if not latest:
            print(f"SIN FUENTE {entry['id']}/{name}: registry no resolvió versión")
            drift = 1
        elif pinned != latest:
            print(f"AVISO {entry['id']}/{name}: pin exacto {pinned}, vigente {latest}")
        else:
            print(f"OK {entry['id']}/{name}: {pinned}")

print("=== Consistencia entre capas ===")
for entry in catalog["templates"]:
    config = root / entry["config_dir"] / entry["pins"]["file"]
    starter = root / entry["starter_dir"] / entry["pins"]["file"]
    parser = PARSERS[entry["pins"]["format"]]
    if config.is_file() and starter.is_file() and parser(config.read_text()) != parser(starter.read_text()):
        print(f"DIVERGENTE {entry['id']}: los pins de config y starter no coinciden")
        drift = 1

print("=== pre-commit vs lockfile ===")
lock_text = (root / "uv.lock").read_text()
locked = dict(re.findall(r'name = "([^"]+)"\nversion = "([^"]+)"', lock_text))
hook_map = {
    "https://github.com/codespell-project/codespell": "codespell",
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
    "https://github.com/PyCQA/bandit": "bandit",
}
hook_lines = (root / ".pre-commit-config.yaml").read_text().splitlines()
checked_hooks = 0
precommit_drift = 0
for i, line in enumerate(hook_lines):
    if not line.strip().startswith("- repo:"):
        continue
    url = line.split("repo:", 1)[1].strip()
    package = hook_map.get(url)
    if not package:
        continue
    checked_hooks += 1
    rev = next((m.group(1) for following in hook_lines[i + 1 : i + 4]
                if (m := re.match(r"\s*rev:\s*(\S+)", following))), None)
    if rev and package in locked and rev.lstrip("v") != locked[package]:
        print(f"PRE-COMMIT DRIFT {package}: rev {rev}, lock {locked[package]}")
        drift = 1
        precommit_drift = 1
if checked_hooks < len(hook_map):
    print(f"SIN FUENTE pre-commit: solo {checked_hooks}/{len(hook_map)} hooks mapeados")
    drift = 1
if not precommit_drift and checked_hooks == len(hook_map):
    print("OK: revs de pre-commit alineados con el lockfile")

raise SystemExit(1 if drift else 0)
PY
