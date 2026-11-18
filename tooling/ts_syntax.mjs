/**
 * Comprueba los archivos TS/TSX de los starters.
 * Usa el `tsc` local de cada starter (TypeScript 7) si `node_modules` está instalado,
 * o el paquete `typescript` global (transpileModule) como respaldo sintáctico.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL("../starters/", import.meta.url));
const templates = ["typescript", "react", "playwright", "puppeteer"];

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    if (["node_modules", "dist", "test-results", "playwright-report"].includes(name)) return [];
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

function loadGlobalTypeScript() {
  try {
    const globalPath = execFileSync("npm", ["root", "-g"], {
      encoding: "utf8",
    }).trim();
    const candidate = join(globalPath, "typescript");
    if (existsSync(candidate)) {
      const mod = require(candidate);
      if (typeof mod.transpileModule === "function") return mod;
    }
  } catch {
    // Ignorar error si npm o typescript global no existen.
  }
  return null;
}

let files = 0;
let failed = 0;
let globalTs;

for (const template of templates) {
  const starterDir = join(root, template);
  const tsFiles = walk(starterDir).filter((item) => /\.(tsx|ts)$/.test(item));
  const localTsc = join(starterDir, "node_modules", ".bin", "tsc");

  if (existsSync(localTsc)) {
    files += tsFiles.length;
    try {
      execFileSync(localTsc, ["--noEmit"], { cwd: starterDir, stdio: "pipe", encoding: "utf8" });
    } catch (error) {
      failed += 1;
      console.error(`${template}: ${error.stdout || error.stderr || error.message}`);
    }
    continue;
  }

  if (globalTs === undefined) globalTs = loadGlobalTypeScript();
  if (!globalTs) {
    console.error(
      `${template}: falta node_modules/.bin/tsc y no hay 'typescript' global con transpileModule.`,
    );
    failed += 1;
    continue;
  }

  for (const path of tsFiles) {
    const result = globalTs.transpileModule(readFileSync(path, "utf8"), {
      fileName: path,
      reportDiagnostics: true,
      compilerOptions: {
        target: globalTs.ScriptTarget.ES2022,
        module: template === "react" ? globalTs.ModuleKind.ESNext : globalTs.ModuleKind.NodeNext,
        jsx: globalTs.JsxEmit.ReactJSX,
      },
    });
    files += 1;
    for (const diagnostic of result.diagnostics ?? []) {
      if (diagnostic.category === globalTs.DiagnosticCategory.Error) {
        failed += 1;
        console.error(
          `${path}: ${globalTs.flattenDiagnosticMessageText(diagnostic.messageText, " ")}`,
        );
      }
    }
  }
}

console.log(`${files} archivos TS/TSX: ${failed} errores`);
process.exitCode = failed ? 1 : 0;
