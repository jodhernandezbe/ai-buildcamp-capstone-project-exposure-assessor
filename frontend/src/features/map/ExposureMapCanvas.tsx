import "maplibre-gl/dist/maplibre-gl.css";

import { Map as MapLibreMap, type StyleSpecification } from "maplibre-gl";

import "./maplibreWorker";
import { useEffect, useRef, useState } from "react";

import { DARK_MODE, REDUCED_MOTION, matches, usePrefers } from "../../lib/usePrefers";
import type { ClientConfig, WorkspaceState } from "../../types/workspace";
import { SOURCES, addOverlays, readPalette, setSourceData } from "./layers";
import { FacilityInspector } from "./FacilityInspector";
import { MapLegend } from "./MapLegend";
import { bufferCollection, facilityCollection, sectorCollection } from "./mapData";

const FIT_PADDING_PX = 64;
const FIT_MAX_ZOOM = 14;
const FIT_DURATION_MS = 900;
const BLANK_STYLE: StyleSpecification = { version: 8, sources: {}, layers: [] };
export const BLANK_NOTICE = "The basemap could not be loaded; facilities are drawn on a blank canvas.";

interface Props {
  workspace: WorkspaceState;
  config: ClientConfig["map"];
  digits: number;
}

function useOverlayData(workspace: WorkspaceState, config: Props["config"]) {
  const scale = { minPx: config.marker_min_px, maxPx: config.marker_max_px };
  return {
    [SOURCES.facilities]: facilityCollection(workspace.facilities, scale),
    [SOURCES.buffers]: bufferCollection(workspace.facilities),
    [SOURCES.sectors]: sectorCollection(workspace.facilities),
  };
}

/** The basemap with the facility markers, receptor circles and schematic downwind sectors. */
export function ExposureMapCanvas({ workspace, config, digits }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const ready = useRef(false);
  const legend = useRef<HTMLElement>(null);
  const [instance, setInstance] = useState<MapLibreMap | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const dark = usePrefers(DARK_MODE);
  const styleUrl = dark ? config.dark_style : config.light_style;
  const data = useOverlayData(workspace, config);
  const latest = useRef({ data, styleUrl, start: config.initial_view });
  useEffect(() => {
    latest.current = { data, styleUrl, start: config.initial_view };
  });

  const draw = () => {
    if (!map.current || !ready.current) return;
    for (const [id, collection] of Object.entries(latest.current.data)) {
      setSourceData(map.current, id, collection);
    }
  };

  useEffect(() => {
    const { start } = latest.current;
    const instance = new MapLibreMap({
      container: container.current as HTMLElement,
      style: latest.current.styleUrl,
      // The configured starting view (the United States) until facilities are placed.
      bounds: [
        [start.west, start.south],
        [start.east, start.north],
      ],
      fitBoundsOptions: { padding: FIT_PADDING_PX },
      attributionControl: { compact: true },
    });
    map.current = instance;
    setInstance(instance);
    instance.on("style.load", () => {
      addOverlays(instance, readPalette());
      ready.current = true;
      draw();
    });
    instance.on("error", (event) => {
      console.warn("Map error:", event.error);
      setNotice(BLANK_NOTICE);
      if (!ready.current) instance.setStyle(BLANK_STYLE);
    });
    return () => {
      ready.current = false;
      instance.remove();
      map.current = null;
      setInstance(null);
    };
    // The map is created once; later changes are applied by the effects below.
  }, []);

  const applied = useRef(styleUrl);
  useEffect(() => {
    if (applied.current === styleUrl || !map.current) return;
    applied.current = styleUrl;
    ready.current = false;
    map.current.setStyle(styleUrl);
  }, [styleUrl]);

  useEffect(draw, [data]);

  const { bounds, framing_version: version } = workspace;
  useEffect(() => {
    if (!map.current || !bounds || version === 0) return;
    map.current.fitBounds(
      [
        [bounds.west, bounds.south],
        [bounds.east, bounds.north],
      ],
      {
        // The legend sits over the bottom-left corner; keep what is framed clear of it.
        padding: {
          top: FIT_PADDING_PX,
          right: FIT_PADDING_PX,
          bottom: FIT_PADDING_PX,
          left: FIT_PADDING_PX + (legend.current?.offsetWidth ?? 0),
        },
        maxZoom: FIT_MAX_ZOOM,
        duration: matches(REDUCED_MOTION) ? 0 : FIT_DURATION_MS,
      },
    );
    // Only a new framing version moves the camera, never other updates of the same bounds.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  return (
    <div className="relative h-full min-h-96 w-full overflow-hidden rounded-2xl border border-hairline">
      {/* Inline, not a utility class: MapLibre's own stylesheet is unlayered, so its
          `position: relative` would beat Tailwind's layered `absolute` and collapse the map. */}
      <div
        ref={container}
        role="region"
        aria-label="Facility map"
        style={{ position: "absolute", inset: 0 }}
      />
      {instance && (
        <FacilityInspector
          map={instance}
          facilities={workspace.facilities}
          scale={{ minPx: config.marker_min_px, maxPx: config.marker_max_px }}
          digits={digits}
        />
      )}
      <MapLegend ref={legend} facilities={workspace.facilities} />
      {notice && (
        <p role="status" className="glass absolute left-3 top-3 m-0 rounded-xl px-3 py-1.5 text-xs text-fg2">
          {notice}
        </p>
      )}
    </div>
  );
}
