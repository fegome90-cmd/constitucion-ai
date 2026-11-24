import { expect, test } from "@playwright/test";

test("incrementa contador", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("0");
  await page.getByRole("button", { name: "Incrementar" }).click();
  await expect(page.getByRole("status")).toHaveText("1");
});
