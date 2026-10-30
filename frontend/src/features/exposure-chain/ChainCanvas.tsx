import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type ReactFlowInstance,
  type Viewport,
} from "@xyflow/react";
import { useEffect, useRef, useState, type RefObject } from "react";

import { ChainNode, type ChainFlowNode } from "./ChainNode";
import { FlowEdge, type FlowFlowEdge } from "./FlowEdge";
import { NODE_H, NODE_W, statusColor, type ExposureGraph } from "./graph";
import type { Positions } from "./layout";
import { MAX_ZOOM, fitZoom, openingViewport } from "./viewport";

const NODE_TYPES = { chain: ChainNode };
const EDGE_TYPES = { flow: FlowEdge };

interface Props {
  graph: ExposureGraph;
  positions: Positions;
  /** Changes with the graph's shape, so the view is fitted again. */
  layoutKey: string;
  digits: number;
  selectedId: string | null;
  activeLane: string | null;
  detailId: string;
  onSelect: (id: string) => void;
  onHover: (lane: string | null) => void;
}

function flowNodes(props: Props): ChainFlowNode[] {
  const { graph, positions, activeLane } = props;
  const laneLabel = (id: string | null) => graph.lanes.find((lane) => lane.id === id)?.label ?? null;
  return graph.nodes.map((node) => ({
    id: node.id,
    type: "chain",
    position: positions.get(node.id) ?? { x: 0, y: 0 },
    width: NODE_W,
    height: NODE_H,
    draggable: false,
    selectable: false,
    focusable: false,
    // React Flow turns pointer events off on nodes that are neither selectable nor draggable;
    // the step inside is a button, so they stay on.
    style: { pointerEvents: "all" },
    data: {
      node,
      laneLabel: laneLabel(node.lane),
      digits: props.digits,
      selected: props.selectedId === node.id,
      dimmed: activeLane !== null && node.lane !== null && node.lane !== activeLane,
      detailId: props.detailId,
      onSelect: props.onSelect,
      onHover: props.onHover,
    },
  }));
}

function flowEdges({ graph, activeLane, digits }: Props): FlowFlowEdge[] {
  const status = (lane: string) => graph.lanes.find((l) => l.id === lane)?.status ?? null;
  return graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: "flow",
    focusable: false,
    data: { quantity: edge.quantity, status: status(edge.lane), dimmed: activeLane !== null && edge.lane !== activeLane, digits },
  }));
}

/** Opens on a readable view and reports the zoom at which everything fits. */
type Instance = ReactFlowInstance<ChainFlowNode, FlowFlowEdge>;

/**
 * Opens on a readable view, and opens it again whenever the canvas changes size (the detail panel
 * opening, the panel resized) until the user pans or zooms themselves. Reports the zoom that fits all.
 */
/** Sets the opening view for the canvas's current size; returns the zoom at which all fits. */
function openView(flow: Instance, element: HTMLElement): number {
  const box = element.getBoundingClientRect();
  const bounds = flow.getNodesBounds(flow.getNodes());
  void flow.setViewport(openingViewport(bounds, box.width, box.height));
  return fitZoom(bounds, box.width, box.height);
}

function useOpening(container: RefObject<HTMLDivElement | null>) {
  const [fitted, setFitted] = useState<number | null>(null);
  const instance = useRef<Instance | null>(null);
  const moved = useRef(false);
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const observer = new ResizeObserver(() => {
      if (instance.current && !moved.current) setFitted(openView(instance.current, element));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [container]);
  const onInit = (flow: Instance) => {
    instance.current = flow;
    if (container.current) setFitted(openView(flow, container.current));
  };
  // Only a gesture has an event; the views set here do not count as the user moving.
  const onMoveStart = (event: MouseEvent | TouchEvent | null) => {
    if (event) moved.current = true;
  };
  return { fitted, onInit, onMoveStart };
}

/**
 * The React Flow canvas: pan, zoom (buttons and pinch) and fit view; the minimap appears only while
 * part of the graph is out of view, so it never hides a step that would otherwise be visible.
 */
export function ChainCanvas(props: Props) {
  const container = useRef<HTMLDivElement>(null);
  const { fitted, onInit, onMoveStart } = useOpening(container);
  const [zoom, setZoom] = useState<number | null>(null);
  const statusOf = new Map(props.graph.lanes.map((lane) => [lane.id, lane.status]));
  const laneOf = new Map(props.graph.nodes.map((n) => [n.id, n.lane]));
  const partial = fitted !== null && zoom !== null && zoom > fitted + 0.01;
  return (
    <div ref={container} className="absolute inset-0">
      <ReactFlowProvider>
        <ReactFlow
          key={props.layoutKey}
          aria-label="Exposure chain diagram"
          nodes={flowNodes(props)}
          edges={flowEdges(props)}
          nodeTypes={NODE_TYPES}
          edgeTypes={EDGE_TYPES}
          onInit={onInit}
          onMoveStart={onMoveStart}
          onMove={(_, viewport: Viewport) => setZoom(viewport.zoom)}
          minZoom={0.2}
          maxZoom={MAX_ZOOM}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          zoomOnScroll={false}
          preventScrolling={false}
          attributionPosition="top-right"
          className="chain-flow-canvas"
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="var(--hairline)" />
          <Controls showInteractive={false} position="bottom-left" fitViewOptions={{ padding: 0.08 }} />
          {partial && (
            <MiniMap
              pannable
              zoomable
              position="bottom-right"
              ariaLabel="Exposure chain overview"
              nodeColor={(node) => statusColor(statusOf.get(laneOf.get(node.id) ?? "") ?? null)}
              className="!h-20 !w-32"
            />
          )}
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
