import { describe, expect, it } from "vitest";

import { FULL_GRAPH } from "../../test/graphs";
import { NODE_H, NODE_W } from "./graph";
import { layoutGraph } from "./layout";

describe("layoutGraph", () => {
  it("places every node, source first and endpoints last, without overlap", async () => {
    const positions = await layoutGraph(FULL_GRAPH);
    expect(positions.size).toBe(FULL_GRAPH.nodes.length);
    const x = (id: string) => positions.get(id)?.x ?? Number.NaN;
    expect(x("source")).toBeLessThan(x("community:air"));
    expect(x("community:air")).toBeLessThan(x("community:endpoint"));
    expect(x("worker:release")).toBeLessThan(x("worker:endpoint"));
    const boxes = [...positions.values()];
    const overlaps = boxes.some((a, i) =>
      boxes.slice(i + 1).some((b) => Math.abs(a.x - b.x) < NODE_W && Math.abs(a.y - b.y) < NODE_H),
    );
    expect(overlaps).toBe(false);
  });

  it("puts each stack and each age band on its own row of the same layer", async () => {
    const positions = await layoutGraph(FULL_GRAPH);
    const one = positions.get("community:stack:1");
    const two = positions.get("community:stack:2");
    expect(one?.x).toBe(two?.x);
    expect(one?.y).not.toBe(two?.y);
  });
});
