#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"

exec python3 - "${REPO_ROOT}" "$@" <<'PY'
import json
import pathlib
import re
import sys
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
from functools import cache

root = pathlib.Path(sys.argv[1])
args = sys.argv[2:]
registry_file = None
usage = "Uso: check-versions.sh [--root <dir>] [--registry-file <archivo.json>]"
if args in (["-h"], ["--help"]):
    print(usage)
    raise SystemExit(0)
while args:
    flag = args.pop(0)
    if flag == "--registry-file" and args:
        registry_file = pathlib.Path(args.pop(0))
    elif flag == "--root" and args:
        root = pathlib.Path(args.pop(0))
    else:
        print(usage, file=sys.stderr)
        raise SystemExit(2)

offline = json.loads(registry_file.read_text()) if registry_file else {}
catalog = json.loads((root / "catalog.json").read_text())

def requirements_pins(requirements):
    result = {}
    for requirement in requirements:
        match = re.fullmatch(r"([a-zA-Z0-9_.-]+)\s*==\s*(\S+)", requirement)
        if match:
            result[match[1]] = match[2]
        else:
            result[requirement] = ""
    return result


def pep440_pins(text):
    config = tomllib.loads(text)
    project = config.get("project", {})
    groups = (
        *config.get("dependency-groups", {}).values(),
        *project.get("optional-dependencies", {}).values(),
    )
    requirements = project.get("dependencies", []) + config.get("build-system", {}).get("requires", [])
    requirements += [
        entry for group in groups for entry in group if isinstance(entry, str)
    ]
    return requirements_pins(requirements)


def npm_pins(text):
    package = json.loads(text)
    dependencies = package.get("dependencies", {}) | package.get("devDependencies", {})
    if "packageManager" in package:
        manager, separator, version = package["packageManager"].partition("@")
        dependencies[manager] = version if separator else ""
    return dependencies


def requirements_file(text):
    return requirements_pins(
        [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    )


PARSERS = {
    "pep440-exact": pep440_pins,
    "npm-exact": npm_pins,
    "luarocks-exact": requirements_file,
    "requirements-exact": requirements_file,
    "rustup-channel": lambda text: {"rust": m.group(1)} if (m := re.search(r'channel\s*=\s*"([^"]+)"', text)) else {},
    "gomod-version": lambda text: {"go": re.search(r"^go\s+(\S+)", text, re.M).group(1)} if re.search(r"^go\s+(\S+)", text, re.M) else {},
}

REGISTRY_URLS = {
    "pypi": lambda n: f"https://pypi.org/pypi/{n}/json",
    "npm": lambda n: f"https://registry.npmjs.org/{n}/latest",
    "maven": lambda n: f"https://repo1.maven.org/maven2/{n.replace(':', '/')}/maven-metadata.xml",
    "rustup": lambda n: "https://static.rust-lang.org/dist/channel-rust-stable.toml",
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


def maven_pins(text):
    pom = ET.fromstring(text)
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    pins = dict.fromkeys(MAVEN_ARTIFACTS, "")
    pins["junit"] = pom.findtext("m:properties/m:junit.version", namespaces=ns) or ""
    plugin_names = {
        artifact.rsplit("/", 1)[-1]: name
        for name, artifact in MAVEN_ARTIFACTS.items()
    }
    for plugin in pom.findall("m:build/m:plugins/m:plugin", ns):
        artifact = plugin.findtext("m:artifactId", namespaces=ns)
        if artifact in plugin_names:
            pins[plugin_names[artifact]] = plugin.findtext("m:version", namespaces=ns) or ""
    pins["google-java-format"] = pom.findtext(".//m:googleJavaFormat/m:version", namespaces=ns) or ""
    # Missing or indirect versions fail the same exact-pin check as ranges.
    return pins


@cache
def resolve(registry, name):
    if registry_file is not None:
        return offline.get(name, "")
    artifact = {"maven": MAVEN_ARTIFACTS, "luarocks": LUA_REPOS}.get(registry, {}).get(name, name)
    try:
        url = REGISTRY_URLS[registry](artifact)
        req = urllib.request.Request(url, headers={"User-Agent": "config-kits-check/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read().decode()
        if registry == "pypi":
            return json.loads(body)["info"]["version"]
        if registry == "npm":
            return json.loads(body)["version"]
        if registry == "maven":
            meta = ET.fromstring(body)
            releases = (
                item.text for item in meta.findall("./versioning/versions/version")
                if item.text and re.fullmatch(r"\d+(?:\.\d+)+", item.text)
            )
            return max(releases, key=lambda v: tuple(map(int, v.split("."))), default="")
        if registry == "rustup":
            return tomllib.loads(body)["pkg"]["rust"]["version"].split()[0]
        if registry == "go":
            return body.splitlines()[0].removeprefix("go")
        if registry == "luarocks":
            return json.loads(body)["tag_name"].removeprefix("v")
    except (OSError, ValueError, KeyError, IndexError, ET.ParseError):
        return ""
    return ""


PARSERS["maven-properties"] = maven_pins

drift = 0
common = root / "templates/_common"
sources = [
    (entry["id"], root / entry["config_dir"] / entry["pins"]["file"], entry["pins"])
    for entry in catalog["templates"]
]
sources += [
    ("_common", common / "requirements-dev.txt", {"format": "requirements-exact", "registry": "pypi"}),
    ("_common", common / "package.json", {"format": "npm-exact", "registry": "npm"}),
]
print("=== Pins por catálogo ===")
for kit, path, pins in sources:
    parser = PARSERS.get(pins["format"])
    registry = pins["registry"]
    if parser is None or registry not in REGISTRY_URLS:
        print(f"SIN FUENTE {kit}: formato '{pins['format']}' o registry '{registry}' desconocido")
        drift = 1
        continue
    if not path.is_file():
        print(f"SIN FUENTE {kit}: falta {path.relative_to(root)}")
        drift = 1
        continue
    try:
        found = parser(path.read_text())
    except (OSError, ValueError, TypeError, ET.ParseError) as exc:
        print(f"SIN FUENTE {kit}: {path.name}: {exc}")
        drift = 1
        continue
    if not found:
        print(f"SIN FUENTE {kit}: no se pudieron extraer pins de {path.name}")
        drift = 1
        continue
    for name, pinned in found.items():
        exact = {
            "go": r"\d+\.\d+(?:\.\d+)?",
            "pypi": r"\d+(?:\.\d+)+(?:\.post\d+)?",
        }.get(registry, r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?")
        if not re.fullmatch(exact, pinned):
            print(f"PIN NO EXACTO {kit}/{name}{f': {pinned}' if pinned else ''}")
            drift = 1
            continue
        latest = resolve(registry, name)
        if not latest:
            print(f"SIN FUENTE {kit}/{name}: registry no resolvió versión")
            drift = 1
        elif pinned != latest:
            print(f"DRIFT {kit}/{name}: pin exacto {pinned}, vigente {latest}")
            drift = 1
        else:
            print(f"OK {kit}/{name}: {pinned}")

print("=== Consistencia entre capas ===")
for entry in catalog["templates"]:
    config = root / entry["config_dir"] / entry["pins"]["file"]
    starter = root / entry["starter_dir"] / entry["pins"]["file"]
    if (
        not config.is_file()
        or config.is_symlink()
        or not starter.is_symlink()
        or starter.readlink().is_absolute()
        or starter.resolve() != config.resolve()
    ):
        print(f"DIVERGENTE {entry['id']}: el starter debe enlazar el descriptor del config kit")
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
