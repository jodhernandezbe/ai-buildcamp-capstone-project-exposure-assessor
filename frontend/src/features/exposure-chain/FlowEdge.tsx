import { BaseEdge, EdgeLabelRenderer, getBezierPath, type Edge, type EdgeProps } from "@xyflow/react";

import { REDUCED_MOTION, usePrefers } from "../../lib/usePrefers";
import { formatQuantity, statusColor, type GraphLane, type GraphQuantity } from "./graph";

export interface FlowEdgeData extends Record<string, unknown> {
  quantity: GraphQuantity | null;
  status: GraphLane["status"];
  dimmed: boolean;
  digits: number;
}

export type FlowFlowEdge = Edge<FlowEdgeData, "flow">;

/** Dots that travel along a connection, evenly spaced (presentation only). */
const PARTICLES = 3;
const PERIOD_S = 2.4;

/**
 * A flowing connection: a curve in the lane's status colour with dots moving from source towards
 * the receptor, and a label with the quantity it carries. Motion stops for reduced-motion users.
 */
export function FlowEdge(props: EdgeProps<FlowFlowEdge>) {
  const { id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data } = props;
  const reduced = usePrefers(REDUCED_MOTION);
  const [path, labelX, labelY] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition });
  const color = statusColor(data?.status ?? null);
  const dimmed = data?.dimmed ?? false;
  const quantity = data?.quantity ?? null;
  return (
    <>
      <BaseEdge id={id} path={path} style={{ stroke: color, strokeWidth: 2, opacity: dimmed ? 0.2 : 0.55 }} />
      {!reduced &&
        !dimmed &&
        Array.from({ length: PARTICLES }, (_, index) => (
          <circle key={index} r={3} fill={color} data-testid="flow-particle">
            <animateMotion dur={`${PERIOD_S}s`} begin={`${(-index * PERIOD_S) / PARTICLES}s`} repeatCount="indefinite" path={path} />
          </circle>
        ))}
      {quantity && (
        <EdgeLabelRenderer>
          <div
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
            className={`pointer-events-none absolute w-max max-w-[136px] rounded-md border border-hairline bg-solid px-1.5 py-0.5 text-center leading-tight shadow-sm ${dimmed ? "opacity-30" : ""}`}
          >
            <span className="block text-[9px] text-fg2">{quantity.label}</span>
            <span className={`block text-[10px] font-medium tabular-nums ${quantity.value === null ? "text-fg2" : "text-fg"}`}>
              {formatQuantity(quantity, data?.digits ?? 2)}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
