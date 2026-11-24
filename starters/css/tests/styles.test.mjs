import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("../src/styles.css", import.meta.url), "utf8");
const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");

test("tokens y layers presentes", () => {
  assert.match(css, /@layer tokens/);
  assert.match(css, /--surface:/);
  assert.match(html, /class="card"/);
});
