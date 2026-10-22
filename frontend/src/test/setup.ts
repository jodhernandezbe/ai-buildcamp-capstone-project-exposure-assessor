import "@testing-library/jest-dom/vitest";

import { vi } from "vitest";

import { StubResizeObserver } from "./fakeResizeObserver";

// jsdom has no WebGL: every test sees the recording stand-in instead of maplibre-gl.
vi.mock("maplibre-gl", async () => {
  const { FakeMap } = await import("./fakeMaplibre");
  return { Map: FakeMap, setWorkerUrl: vi.fn() };
});

// Assigned, not stubbed, so tests that call `vi.unstubAllGlobals()` keep it.
globalThis.ResizeObserver = StubResizeObserver as unknown as typeof ResizeObserver;
