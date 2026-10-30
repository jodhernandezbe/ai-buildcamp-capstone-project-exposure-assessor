import { useEffect, useState } from "react";

import { shapeKey, type ExposureGraph } from "./graph";
import { layoutGraph, type Positions } from "./layout";

/** The layout of the graph's current shape; null while it is being computed. */
export function useGraphLayout(graph: ExposureGraph | null): { positions: Positions | null; key: string } {
  const key = graph ? shapeKey(graph) : "";
  const [done, setDone] = useState<{ key: string; positions: Positions } | null>(null);
  useEffect(() => {
    if (!graph) return;
    let live = true;
    void layoutGraph(graph).then((positions) => {
      if (live) setDone({ key, positions });
    });
    return () => {
      live = false;
    };
    // The key captures the graph's shape; values that change without moving nodes need no relayout.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return { positions: done?.key === key ? done.positions : null, key };
}
