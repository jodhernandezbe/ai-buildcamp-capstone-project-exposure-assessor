import { useSyncExternalStore } from "react";

function query(media: string): MediaQueryList | null {
  return typeof window !== "undefined" && window.matchMedia ? window.matchMedia(media) : null;
}

/** Whether a media query matches now (false where media queries are unavailable). */
export const matches = (media: string): boolean => query(media)?.matches ?? false;

/** Follows a media query such as `(prefers-color-scheme: dark)` as the OS setting changes. */
export function usePrefers(media: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const list = query(media);
      list?.addEventListener("change", onChange);
      return () => list?.removeEventListener("change", onChange);
    },
    () => matches(media),
    () => false,
  );
}

export const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";
export const DARK_MODE = "(prefers-color-scheme: dark)";
