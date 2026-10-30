import ELK from "elkjs/lib/elk.bundled.js";

import { NODE_H, NODE_W, type ExposureGraph } from "./graph";

export type Positions = ReadonlyMap<string, { x: number; y: number }>;

/** Layered left-to-right layout; the gap between layers leaves room for the edge labels. */
export const LAYOUT_OPTIONS: Record<string, string> = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.layered.spacing.nodeNodeBetweenLayers": "140",
  "elk.spacing.nodeNode": "28",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
  "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
};

const elk = new ELK();

/** Top-left position of every node, from ELK (presentation only; no value is read). */
export async function layoutGraph(graph: ExposureGraph): Promise<Positions> {
  const result = await elk.layout({
    id: "root",
    layoutOptions: LAYOUT_OPTIONS,
    children: graph.nodes.map((node) => ({ id: node.id, width: NODE_W, height: NODE_H })),
    edges: graph.edges.map((edge) => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
  });
  return new Map((result.children ?? []).map((child) => [child.id, { x: child.x ?? 0, y: child.y ?? 0 }]));
}
