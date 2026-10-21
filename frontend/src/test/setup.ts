import "@testing-library/jest-dom/vitest";

import { vi } from "vitest";

// jsdom has no WebGL: every test sees the recording stand-in instead of maplibre-gl.
vi.mock("maplibre-gl", async () => {
  const { FakeMap } = await import("./fakeMaplibre");
  return { Map: FakeMap, setWorkerUrl: vi.fn() };
});
