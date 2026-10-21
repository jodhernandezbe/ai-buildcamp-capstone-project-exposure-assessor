import type { Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useId, useReducer, useRef, useState } from "react";

import type { Facility } from "../../types/workspace";
import { FacilityHoverCard } from "./FacilityHoverCard";
import { type MarkerScale, facilityCollection } from "./mapData";

// Room the card needs beside and above a marker; it flips to the other side without it (px).
const CARD_WIDTH_PX = 336;
const CARD_HEIGHT_PX = 420;
const GAP_PX = 12;

interface Active {
  frsId: string;
  flipX: boolean;
  flipY: boolean;
}

function useMapMoves(map: MapLibreMap): void {
  const [, redraw] = useReducer((n: number) => n + 1, 0);
  useEffect(() => {
    map.on("move", redraw);
    map.on("resize", redraw);
    return () => {
      map.off("move", redraw);
      map.off("resize", redraw);
    };
  }, [map]);
}

/**
 * One keyboard-focusable button over every marker (a canvas marker cannot take focus), and the
 * glass card of the facility that is hovered or focused. Escape, leaving or blurring closes it.
 */
export function FacilityInspector({
  map,
  facilities,
  scale,
  digits,
}: {
  map: MapLibreMap;
  facilities: Facility[];
  scale: MarkerScale;
  digits: number;
}) {
  const overlay = useRef<HTMLDivElement>(null);
  const cardId = useId();
  const [active, setActive] = useState<Active | null>(null);
  useMapMoves(map);

  useEffect(() => {
    if (!active) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setActive(null);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [active]);

  const radii = facilityCollection(facilities, scale).features;
  const open = (facility: Facility, x: number, y: number) => {
    const box = overlay.current?.getBoundingClientRect();
    setActive({
      frsId: facility.frs_id,
      flipX: box ? box.width - x < CARD_WIDTH_PX + GAP_PX : false,
      flipY: y < CARD_HEIGHT_PX + GAP_PX,
    });
  };
  const close = (frsId: string) => setActive((now) => (now?.frsId === frsId ? null : now));

  return (
    <div ref={overlay} className="pointer-events-none absolute inset-0 z-10 overflow-hidden">
      {facilities.map((facility, index) => {
        const { x, y } = map.project([facility.longitude, facility.latitude]);
        const radius = radii[index]?.properties.radius_px ?? scale.minPx;
        const isActive = active?.frsId === facility.frs_id;
        return (
          <div key={facility.frs_id}>
            <button
              type="button"
              aria-label={`${facility.name ?? `FRS ${facility.frs_id}`}, ${facility.status ?? "risk not computed"}`}
              aria-describedby={isActive ? cardId : undefined}
              className="pointer-events-auto absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-full bg-transparent"
              style={{ left: x, top: y, width: radius * 2, height: radius * 2 }}
              onMouseEnter={() => open(facility, x, y)}
              onMouseLeave={() => close(facility.frs_id)}
              onFocus={() => open(facility, x, y)}
              onBlur={() => close(facility.frs_id)}
            />
            {isActive && active && (
              <div
                className="absolute"
                style={{
                  left: x + (active.flipX ? -(radius + GAP_PX) : radius + GAP_PX),
                  top: y,
                  transform: `translate(${active.flipX ? "-100%" : "0"}, ${active.flipY ? "0" : "-100%"})`,
                }}
              >
                <FacilityHoverCard facility={facility} digits={digits} id={cardId} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
