// A stand-in for maplibre-gl (jsdom has no WebGL): records what the app asks the map to do.
type Handler = (event?: unknown) => void;

export interface FitCall {
  bounds: [[number, number], [number, number]];
  options: {
    padding?: number | { top: number; right: number; bottom: number; left: number };
    maxZoom?: number;
    duration?: number;
  };
}

export class FakeMap {
  static instances: FakeMap[] = [];
  options: Record<string, unknown>;
  handlers = new Map<string, Handler[]>();
  sources = new Map<string, { data: unknown; setData: (d: unknown) => void }>();
  layers = new Set<string>();
  styles: unknown[] = [];
  fits: FitCall[] = [];
  removed = false;

  constructor(options: Record<string, unknown>) {
    this.options = options;
    this.styles.push(options.style);
    FakeMap.instances.push(this);
  }

  static reset(): void {
    FakeMap.instances = [];
  }

  static get last(): FakeMap {
    return FakeMap.instances.at(-1) as FakeMap;
  }

  on(event: string, handler: Handler): this {
    this.handlers.set(event, [...(this.handlers.get(event) ?? []), handler]);
    return this;
  }

  off(event: string, handler: Handler): this {
    this.handlers.set(
      event,
      (this.handlers.get(event) ?? []).filter((h) => h !== handler),
    );
    return this;
  }

  /** A fixed projection: 10 px per degree from the origin, so tests know where markers sit. */
  project(lngLat: [number, number]): { x: number; y: number } {
    return { x: 500 + lngLat[0] * 10, y: 500 - lngLat[1] * 10 };
  }

  emit(event: string, payload?: unknown): void {
    for (const handler of this.handlers.get(event) ?? []) handler(payload);
  }

  addSource(id: string, spec: { data: unknown }): void {
    const source = {
      data: spec.data,
      setData(d: unknown) {
        source.data = d;
      },
    };
    this.sources.set(id, source);
  }

  getSource(id: string) {
    return this.sources.get(id);
  }

  addLayer(layer: { id: string }): void {
    this.layers.add(layer.id);
  }

  getLayer(id: string): { id: string } | undefined {
    return this.layers.has(id) ? { id } : undefined;
  }

  setStyle(style: unknown): void {
    this.styles.push(style);
    this.sources.clear();
    this.layers.clear();
  }

  fitBounds(bounds: FitCall["bounds"], options: FitCall["options"]): void {
    this.fits.push({ bounds, options });
  }

  remove(): void {
    this.removed = true;
  }
}
