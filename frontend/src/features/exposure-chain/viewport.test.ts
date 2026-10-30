import { describe, expect, it } from "vitest";

import { MAX_ZOOM, PADDING_PX, READABLE_ZOOM, fitZoom, openingViewport } from "./viewport";

const bounds = { x: 0, y: 0, width: 1000, height: 400 };

describe("viewport", () => {
  it("fits the whole graph in a wide canvas, centred", () => {
    const view = openingViewport(bounds, 1248, 600);
    expect(view.zoom).toBeCloseTo((1248 - 2 * PADDING_PX) / 1000);
    expect(view.x).toBeCloseTo((1248 - 1000 * view.zoom) / 2);
  });

  it("never zooms in past the maximum", () => {
    expect(fitZoom({ x: 0, y: 0, width: 100, height: 50 }, 1200, 800)).toBe(MAX_ZOOM);
  });

  it("opens a narrow canvas at a readable zoom with the source at the left edge", () => {
    const view = openingViewport({ ...bounds, x: 50 }, 560, 600);
    expect(view.zoom).toBe(READABLE_ZOOM);
    expect(view.x).toBeCloseTo(PADDING_PX - 50 * READABLE_ZOOM);
  });
});
