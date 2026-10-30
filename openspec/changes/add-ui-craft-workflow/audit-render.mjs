// UI audit renderer: drives the live app with Playwright in light and dark, saves screenshots
// per surface/state/scheme, and prints an accessibility summary. Changes nothing in the app.
import { chromium } from "/Users/josehernandez/Documents/ai-buildcamp-capstone-project-exposure-assessor/frontend/node_modules/playwright/index.mjs";
import { mkdirSync } from "node:fs";

const BASE = "http://127.0.0.1:8000";
const OUT = new URL("./shots/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });

async function waitForServer() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(BASE + "/");
      if (r.ok) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error("server not reachable");
}

async function step(name, fn) {
  try {
    await fn();
    console.log("ok   " + name);
  } catch (e) {
    console.log("skip " + name + ": " + String(e.message ?? e).split("\n")[0]);
  }
}

async function run(scheme) {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ colorScheme: scheme, viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const shot = (n) => page.screenshot({ path: `${OUT}${n}-${scheme}.png` });
  const settle = () => page.waitForTimeout(700);

  await page.goto(BASE, { waitUntil: "networkidle" });
  await settle();
  await shot("app-first-load");

  if (scheme === "light") {
    const buttons = await page.locator("button, [role=button], a[href]").evaluateAll((els) =>
      els.map((e) => ({
        name: (e.getAttribute("aria-label") || e.textContent || "").trim().slice(0, 40),
        title: e.getAttribute("title"),
        visible: !!(e.offsetWidth || e.offsetHeight),
      })),
    );
    const unnamed = buttons.filter((b) => b.visible && !b.name && !b.title);
    console.log(`controls visible: ${buttons.filter((b) => b.visible).length}, unnamed: ${unnamed.length}`);
    const landmarks = await page.locator("header, nav, main, aside, [role=region], [role=group], h1, h2").evaluateAll((els) =>
      els.map((e) => `${e.tagName.toLowerCase()}${e.getAttribute("role") ? "[" + e.getAttribute("role") + "]" : ""}:${(e.getAttribute("aria-label") || e.textContent || "").trim().slice(0, 40)}`),
    );
    console.log("landmarks: " + landmarks.join(" | "));
    const live = await page.locator("[aria-live], [role=status], [role=alert]").count();
    console.log("live regions: " + live);
  }

  await step("settings drawer", async () => {
    await page.getByRole("button", { name: /settings/i }).first().click();
    await settle();
    await shot("settings-drawer");
    await page.keyboard.press("Escape");
    await settle();
  });

  await step("monitoring", async () => {
    await page.getByRole("button", { name: /monitoring/i }).first().click();
    await page.waitForTimeout(1500);
    await shot("monitoring");
    await page.getByRole("button", { name: /workspace|overview/i }).first().click();
    await settle();
  });

  await step("copilot hidden", async () => {
    await page.getByRole("button", { name: /copilot/i }).first().click();
    await settle();
    await shot("app-copilot-hidden");
    await page.getByRole("button", { name: /copilot/i }).first().click();
    await settle();
  });

  await step("overview fullscreen", async () => {
    await page.getByRole("button", { name: /enter fullscreen/i }).first().click();
    await settle();
    await shot("overview-fullscreen");
    await page.keyboard.press("Escape");
    await settle();
  });

  await step("map fullscreen", async () => {
    await page.getByRole("button", { name: /enter fullscreen/i }).nth(1).click();
    await settle();
    await shot("map-fullscreen");
    await page.keyboard.press("Escape");
    await settle();
  });

  await step("composer with text", async () => {
    const box = page.getByRole("textbox", { name: /message/i }).first();
    await box.click();
    await box.fill("Assess benzene releases near Houston, TX");
    await settle();
    await shot("chat-composer-filled");
    await box.fill("");
  });

  await step("keyboard focus", async () => {
    await page.mouse.click(5, 5);
    for (let i = 0; i < 3; i++) await page.keyboard.press("Tab");
    await settle();
    await shot("focus-third-tab");
    const focused = await page.evaluate(() => {
      const e = document.activeElement;
      return e ? `${e.tagName.toLowerCase()} "${e.getAttribute("aria-label") || e.textContent?.trim().slice(0, 30)}" outline=${getComputedStyle(e).outlineStyle}` : "none";
    });
    console.log("focused after 3 tabs: " + focused);
  });

  await step("narrow viewport", async () => {
    await page.setViewportSize({ width: 720, height: 900 });
    await settle();
    await shot("app-narrow");
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  await browser.close();
}

await waitForServer();
for (const scheme of ["light", "dark"]) {
  console.log(`== ${scheme} ==`);
  await run(scheme);
}
