import type { Feature, FeatureCollection, Point, Polygon } from "geojson";

import type { Facility, Status } from "../../types/workspace";

export interface MarkerScale {
  minPx: number;
  maxPx: number;
}

export interface MarkerProperties {
  frs_id: string;
  name: string;
  status: Status | "none";
  radius_px: number;
}

/** Marker radius (px) from the emission rate, on a square-root scale across the facilities shown. */
export function markerRadius(rate: number, rates: number[], scale: MarkerScale): number {
  const roots = rates.map((r) => Math.sqrt(Math.max(r, 0)));
  const low = Math.min(...roots);
  const high = Math.max(...roots);
  if (!(high > low)) return (scale.minPx + scale.maxPx) / 2;
  const share = (Math.sqrt(Math.max(rate, 0)) - low) / (high - low);
  return scale.minPx + (scale.maxPx - scale.minPx) * share;
}

/** One point per facility: coloured by status (none while not computed), sized by emission rate. */
export function facilityCollection(
  facilities: Facility[],
  scale: MarkerScale,
): FeatureCollection<Point, MarkerProperties> {
  const rates = facilities.map((f) => f.emission_rate_g_s);
  return {
    type: "FeatureCollection",
    features: facilities.map((f) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [f.longitude, f.latitude] },
      properties: {
        frs_id: f.frs_id,
        name: f.name ?? `FRS ${f.frs_id}`,
        status: f.status ?? "none",
        radius_px: markerRadius(f.emission_rate_g_s, rates, scale),
      },
    })),
  };
}

function polygons(
  facilities: Facility[],
  pick: (facility: Facility) => Polygon | null,
): FeatureCollection<Polygon, { frs_id: string }> {
  const features: Feature<Polygon, { frs_id: string }>[] = [];
  for (const facility of facilities) {
    const shape = pick(facility);
    if (shape) features.push({ type: "Feature", geometry: shape, properties: { frs_id: facility.frs_id } });
  }
  return { type: "FeatureCollection", features };
}

/** The receptor radius circles of the facilities that have receptors. */
export const bufferCollection = (facilities: Facility[]) => polygons(facilities, (f) => f.buffer);

/** The schematic downwind sectors of the facilities that have receptors and weather. */
export const sectorCollection = (facilities: Facility[]) => polygons(facilities, (f) => f.sector);
