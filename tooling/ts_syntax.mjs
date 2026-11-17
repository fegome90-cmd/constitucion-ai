/**
 * Comprueba la sintaxis TS/TSX con el TypeScript global del host, sin resolver imports.
 * No es typecheck y no reemplaza `pnpm typecheck`.
 */
import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const globalPath = execFileSync("npm", ["root", "-g"], {
  encoding: "utf8",
}).trim();
const ts = require(join(globalPath, "typescript"));

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

const root = fileURLToPath(new URL("../templates/", import.meta.url));
let files = 0;
let failed = 0;
for (const template of ["typescript", "react", "playwright", "puppeteer"]) {
  for (const path of walk(join(root, template)).filter((item) => /\.(tsx|ts)$/.test(item))) {
    const result = ts.transpileModule(readFileSync(path, "utf8"), {
      fileName: path,
      reportDiagnostics: true,
      compilerOptions: {
        target: ts.ScriptTarget.ES2022,
        module: ts.ModuleKind.ESNext,
        jsx: ts.JsxEmit.ReactJSX,
      },
    });
    files += 1;
    for (const diagnostic of result.diagnostics ?? []) {
      if (diagnostic.category === ts.DiagnosticCategory.Error) {
        failed += 1;
        console.error(`${path}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, " ")}`);
      }
    }
  }
}
console.log(`${files} archivos TS/TSX: ${failed} errores sintácticos`);
process.exitCode = failed ? 1 : 0;
