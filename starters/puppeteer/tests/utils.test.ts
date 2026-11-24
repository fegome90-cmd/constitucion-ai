import assert from "node:assert/strict";
import test from "node:test";
import { title } from "../src/utils.js";

test("normaliza título", () => {
  assert.equal(title(" demo "), "demo");
});

test("rechaza título vacío", () => {
  assert.throws(() => title("   "));
});
