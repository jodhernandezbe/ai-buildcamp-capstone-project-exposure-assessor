import type { Rect, Viewport } from "@xyflow/react";

/** Below this zoom node text is too small to read; a narrow panel starts here and pans. */
export const READABLE_ZOOM = 0.6;
export const MAX_ZOOM = 1.4;
export const PADDING_PX = 24;

/** The zoom at which the whole graph fits the canvas. */
export function fitZoom(bounds: Rect, width: number, height: number): number {
  if (bounds.width <= 0 || bounds.height <= 0) return MAX_ZOOM;
  const zoom = Math.min((width - 2 * PADDING_PX) / bounds.width, (height - 2 * PADDING_PX) / bounds.height);
  return Math.max(Math.min(zoom, MAX_ZOOM), 0);
}

/**
 * The opening view: the whole graph centred when it fits at a readable zoom; otherwise the readable
 * zoom with the source (leftmost) at the left edge, vertically centred, for the user to pan along.
 */
export function openingViewport(bounds: Rect, width: number, height: number): Viewport {
  const fitted = fitZoom(bounds, width, height);
  const zoom = fitted >= READABLE_ZOOM ? fitted : READABLE_ZOOM;
  const x = fitted >= READABLE_ZOOM ? (width - bounds.width * zoom) / 2 - bounds.x * zoom : PADDING_PX - bounds.x * zoom;
  const y = (height - bounds.height * zoom) / 2 - bounds.y * zoom;
  return { x, y, zoom };
}
