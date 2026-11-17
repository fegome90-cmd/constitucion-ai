import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("incrementa al pulsar", () => {
    render(<App />);
    const button = screen.getByRole("button", { name: "Incrementar: 0" });
    fireEvent.click(button);
    expect(screen.getByRole("button", { name: "Incrementar: 1" })).toBeTruthy();
  });
});
