import { describe, expect, it } from "vitest";
import { greet } from "../src/index.js";

describe("greet", () => {
  it("saluda", () => {
    expect(greet(" mundo ")).toBe("Hola, mundo");
  });
  it("rechaza vacío", () => {
    expect(() => greet(" ")).toThrow();
  });
});
