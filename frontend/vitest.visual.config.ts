/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vite";

// Visual tests: real Chromium (Playwright), light and dark, each screenshot compared with the
// approved reference under __screenshots__/. Approve a deliberate change with `-u` after looking.
const VIEWPORT = { width: 1320, height: 900 };

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    include: ["src/**/*.visual.tsx"],
    browser: {
      enabled: true,
      headless: true,
      viewport: VIEWPORT,
      instances: [
        { browser: "chromium", name: "light", provider: playwright({ contextOptions: { colorScheme: "light" } }) },
        { browser: "chromium", name: "dark", provider: playwright({ contextOptions: { colorScheme: "dark" } }) },
      ],
      expect: { toMatchScreenshot: { comparatorName: "pixelmatch", comparatorOptions: { allowedMismatchedPixelRatio: 0.01 } } },
    },
  },
});
