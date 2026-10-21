/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type ProxyOptions } from "vite";

// The API serves dist/ in production. In `npm run dev` requests to /api go to the API on its
// configured loopback address ([ui] host and port in config/settings.toml); override with
// API_URL if those change. The API only accepts writes from its own origin, so the proxy
// presents that origin instead of the dev server's.
const api = process.env.API_URL ?? "http://127.0.0.1:8000";
const apiProxy: ProxyOptions = {
  target: api,
  changeOrigin: true,
  configure: (server) => {
    server.on("proxyReq", (request) => request.setHeader("origin", api));
  },
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": apiProxy } },
  build: { outDir: "dist", sourcemap: false },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/test/setup.ts"],
    css: false,
  },
});
