/**
 * What React Flow measures that jsdom lacks (its documented test setup): a DOMMatrixReadOnly that
 * reads the scale, element sizes from inline styles, and an empty SVG bounding box.
 */
export function installReactFlowStubs(): void {
  class StubMatrix {
    m22: number;
    constructor(transform?: string) {
      const scale = transform?.match(/scale\(([0-9.]+)\)/)?.[1];
      this.m22 = scale !== undefined ? Number(scale) : 1;
    }
  }
  globalThis.DOMMatrixReadOnly = StubMatrix as unknown as typeof DOMMatrixReadOnly;
  Object.defineProperties(HTMLElement.prototype, {
    offsetHeight: { configurable: true, get(this: HTMLElement) { return Number.parseFloat(this.style.height) || 1; } },
    offsetWidth: { configurable: true, get(this: HTMLElement) { return Number.parseFloat(this.style.width) || 1; } },
  });
  (SVGElement.prototype as unknown as { getBBox: () => DOMRect }).getBBox = () => ({ x: 0, y: 0, width: 0, height: 0 }) as DOMRect;
}
