import { useCallback, useEffect, useState } from "react";

import type { Fullscreen } from "./PanelFrame";

/**
 * Which panel is fullscreen. Escape leaves fullscreen unless a layer above it (an inspector,
 * a drawer) already handled the key.
 */
export function useFullscreen() {
  const [fullscreen, setFullscreen] = useState<Fullscreen>(null);
  const toggle = useCallback(
    (id: "overview" | "map") => setFullscreen((now) => (now === id ? null : id)),
    [],
  );
  const exit = useCallback(() => setFullscreen(null), []);

  useEffect(() => {
    if (fullscreen === null) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented) setFullscreen(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreen]);

  return { fullscreen, toggle, exit };
}
