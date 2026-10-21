import { setWorkerUrl } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";

// MapLibre looks for its worker file next to its own module. Once Vite bundles the app that file
// is not there and the worker fails to load, so nothing is drawn: no basemap, no overlays. Point
// MapLibre at the copy Vite emits instead. Imported once, for this side effect, before any map.
setWorkerUrl(workerUrl);

export { workerUrl };
