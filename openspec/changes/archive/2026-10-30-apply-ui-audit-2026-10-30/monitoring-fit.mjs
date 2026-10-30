// Measures whether the Monitoring sessions table fits its pane at several window widths.
import { chromium } from "/Users/josehernandez/Documents/ai-buildcamp-capstone-project-exposure-assessor/frontend/node_modules/playwright/index.mjs";

const OUT = new URL("./shots/", import.meta.url).pathname;
for (let i = 0; i < 120; i++) {
  try {
    if ((await fetch("http://127.0.0.1:8000/")).ok) break;
  } catch {}
  await new Promise((r) => setTimeout(r, 500));
}
const browser = await chromium.launch();
for (const width of [1280, 1440, 1920]) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  await page.goto("http://127.0.0.1:8000", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /monitoring/i }).first().click();
  await page.waitForSelector("table");
  await page.waitForTimeout(800);
  const fit = await page.evaluate(() => {
    const box = document.querySelector("table")?.parentElement;
    const visible = [...document.querySelectorAll("thead th")]
      .filter((th) => getComputedStyle(th).display !== "none")
      .map((th) => th.textContent);
    return { scroll: box?.scrollWidth, client: box?.clientWidth, visible };
  });
  console.log(`${width}px: overflow=${(fit.scroll ?? 0) > (fit.client ?? 0)} (${fit.scroll}/${fit.client}) columns=${fit.visible.join(", ")}`);
  await page.screenshot({ path: `${OUT}monitoring-${width}.png` });
  await page.close();
}
await browser.close();
