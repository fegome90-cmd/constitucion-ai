import puppeteer from "puppeteer";
import { title } from "./utils.js";

async function main(): Promise<void> {
  const browser = await puppeteer.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.setContent("<h1>Automatización lista</h1>");
    const heading = await page.$eval(
      "h1",
      (el) => el.textContent?.trim() ?? "",
    );
    console.log(title(heading));
  } finally {
    await browser.close();
  }
}

await main();
