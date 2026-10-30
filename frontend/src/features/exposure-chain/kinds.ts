import { Activity, ArrowUpFromDot, Factory, Gauge, Users, Wind, type LucideIcon } from "lucide-react";

import type { GraphNode } from "./graph";

/** Icon and badge of each kind of step (presentation only; titles and values come from the API). */
export const KINDS: Record<GraphNode["kind"], { icon: LucideIcon; badge: string }> = {
  source: { icon: Factory, badge: "Source" },
  release: { icon: ArrowUpFromDot, badge: "Release" },
  pathway: { icon: Wind, badge: "Pathway" },
  route: { icon: Activity, badge: "Route" },
  receptor: { icon: Users, badge: "Receptor" },
  endpoint: { icon: Gauge, badge: "Endpoint" },
};
