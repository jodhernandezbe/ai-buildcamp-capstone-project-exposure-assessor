import { facility } from "../../test/fixtures";
import {
  bufferCollection,
  facilityCollection,
  markerRadius,
  sectorCollection,
} from "./mapData";

const scale = { minPx: 6, maxPx: 22 };

describe("markerRadius", () => {
  it("maps the smallest and largest rate to the configured radii", () => {
    const rates = [1, 4, 9];
    expect(markerRadius(1, rates, scale)).toBe(6);
    expect(markerRadius(9, rates, scale)).toBe(22);
  });

  it("scales by the square root, so area follows the rate", () => {
    expect(markerRadius(4, [1, 4, 9], scale)).toBe(14);
  });

  it("uses the middle radius when every rate is equal or there is one facility", () => {
    expect(markerRadius(5, [5], scale)).toBe(14);
    expect(markerRadius(5, [5, 5], scale)).toBe(14);
  });

  it("treats a negative rate as zero", () => {
    expect(markerRadius(-3, [-3, 4], scale)).toBe(6);
  });
});

describe("facilityCollection", () => {
  it("places one point per facility at its longitude and latitude", () => {
    const data = facilityCollection([facility({ longitude: -20, latitude: 10 })], scale);
    expect(data.features).toHaveLength(1);
    expect(data.features[0]?.geometry.coordinates).toEqual([-20, 10]);
  });

  it("colours by status and is neutral while no risk is computed", () => {
    const data = facilityCollection(
      [facility({ frs_id: "A", status: "above" }), facility({ frs_id: "B", status: null })],
      scale,
    );
    expect(data.features.map((f) => f.properties.status)).toEqual(["above", "none"]);
  });

  it("falls back to the FRS ID for an unnamed facility", () => {
    const data = facilityCollection([facility({ name: null })], scale);
    expect(data.features[0]?.properties.name).toBe("FRS F1");
  });

  it("sizes by emission rate", () => {
    const data = facilityCollection(
      [facility({ frs_id: "A", emission_rate_g_s: 1 }), facility({ frs_id: "B", emission_rate_g_s: 9 })],
      scale,
    );
    expect(data.features.map((f) => f.properties.radius_px)).toEqual([6, 22]);
  });
});

describe("overlay collections", () => {
  const ring = { type: "Polygon" as const, coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] };

  it("includes only facilities that have the shape", () => {
    const facilities = [
      facility({ frs_id: "A", buffer: ring, sector: ring }),
      facility({ frs_id: "B", buffer: ring }),
      facility({ frs_id: "C" }),
    ];
    expect(bufferCollection(facilities).features.map((f) => f.properties.frs_id)).toEqual(["A", "B"]);
    expect(sectorCollection(facilities).features.map((f) => f.properties.frs_id)).toEqual(["A"]);
  });
});
