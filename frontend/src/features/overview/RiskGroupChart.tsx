import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatNumber } from "../../lib/format";
import type { Thresholds } from "../../types/api";
import { describeBar, type Group, type Quantity } from "./riskGroups";

const HQ_COLOR = "var(--accent)";
const RISK_COLOR = "var(--series-cancer)";
const AXIS_TEXT = { fill: "var(--fg-2)", fontSize: 11 };

interface ChartRow {
  label: string;
  group: Group;
  /** Only a positive value can be drawn on a logarithmic axis; others stay in the text. */
  hq?: number;
  risk?: number;
}

const drawable = (value: number | undefined): number | undefined =>
  value !== undefined && value > 0 ? value : undefined;

export const toRows = (groups: Group[]): ChartRow[] =>
  groups.map((group) => ({
    label: group.label,
    group,
    hq: drawable(group.hq?.value),
    risk: drawable(group.risk?.value),
  }));

/** An axis tick: plain digits, or a compact 1e-4 where scientific notation would not fit. */
const compactTick = (value: number): string =>
  value !== 0 && (Math.abs(value) < 1e-3 || Math.abs(value) >= 1e5)
    ? value.toExponential(0)
    : formatNumber(value, 2);

const shorten = (text: string, max: number): string => (text.length > max ? `${text.slice(0, max - 1)}…` : text);

interface TooltipProps {
  active?: boolean;
  payload?: readonly { dataKey?: unknown; payload?: unknown }[];
  digits: number;
}

/** The hover card of one bar: the value, the facility behind it, its concentration, the counts. */
export function BarTooltip({ active, payload, digits }: TooltipProps) {
  const entry = payload?.[0];
  if (!active || !entry) return null;
  const quantity: Quantity = entry.dataKey === "risk" ? "risk" : "hq";
  const row = entry.payload as ChartRow | undefined;
  if (!row) return null;
  const [title, ...lines] = describeBar(row.group, quantity, digits);
  return (
    <div className="glass max-w-64 rounded-xl p-2.5 text-xs shadow-[var(--shadow)]">
      <p className="m-0 font-semibold">{title}</p>
      {lines.map((line) => (
        <p key={line} className="m-0 text-fg2">
          {line}
        </p>
      ))}
    </div>
  );
}

function Legend({ thresholds, digits }: { thresholds: Thresholds | undefined; digits: number }) {
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-3 gap-y-0.5 p-0 text-[11px] text-fg2">
      <li className="flex items-center gap-1">
        <span aria-hidden className="inline-block size-2 rounded-sm" style={{ background: HQ_COLOR }} />
        Hazard quotient (non-cancer)
      </li>
      <li className="flex items-center gap-1">
        <span aria-hidden className="inline-block size-2 rounded-sm" style={{ background: RISK_COLOR }} />
        Lifetime cancer risk
      </li>
      {thresholds && (
        <li>
          Dashed: thresholds of concern (HQ {formatNumber(thresholds.hq_concern, digits)}, cancer risk{" "}
          {formatNumber(thresholds.cancer_lower, digits)} to {formatNumber(thresholds.cancer_upper, digits)})
        </li>
      )}
    </ul>
  );
}

/** The same bars as text, for screen readers and for values a log axis cannot draw. */
function BarsAsText({ groups, digits, caption }: { groups: Group[]; digits: number; caption: string }) {
  // The wrapper clips it: a table ignores its own width, so `sr-only` on the table alone left a
  // 1300 px wide box that made the panel scroll sideways.
  return (
    <div className="sr-only">
    <table>
      <caption>{caption}</caption>
      <thead>
        <tr>
          <th scope="col">Group</th>
          <th scope="col">Highest worst-case hazard quotient</th>
          <th scope="col">Highest worst-case lifetime cancer risk</th>
          <th scope="col">Facilities</th>
          <th scope="col">Assessed</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g) => (
          <tr key={g.key}>
            <th scope="row">{g.label}</th>
            <td>{g.hq ? `${formatNumber(g.hq.value, digits)} (${g.hq.name ?? g.hq.frsId})` : "not reported"}</td>
            <td>{g.risk ? `${formatNumber(g.risk.value, digits)} (${g.risk.name ?? g.risk.frsId})` : "not reported"}</td>
            <td>{g.facilities}</td>
            <td>{g.assessed}</td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

interface Props {
  groups: Group[];
  thresholds: Thresholds | undefined;
  digits: number;
  /** What the chart is of, for assistive technology. */
  caption: string;
  /** Characters of an x-axis label shown before it is cut (the tooltip and text have it all). */
  labelChars: number;
  /** Tailwind classes for the plot area's height. */
  heightClass: string;
  /** Angle the x-axis labels (a narrow chart); wide charts keep them level. */
  angled: boolean;
}

/** Two bars per group (worst-case HQ left axis, cancer risk right axis), each axis logarithmic. */
export function RiskGroupChart({ groups, thresholds, digits, caption, labelChars, heightClass, angled }: Props) {
  const lines = thresholds
    ? [
        { y: thresholds.hq_concern, axis: "hq", color: HQ_COLOR, text: `HQ ${formatNumber(thresholds.hq_concern, digits)}`, at: "insideTopLeft" as const },
        { y: thresholds.cancer_lower, axis: "risk", color: RISK_COLOR, text: `risk ${compactTick(thresholds.cancer_lower)}`, at: "insideTopRight" as const },
        { y: thresholds.cancer_upper, axis: "risk", color: RISK_COLOR, text: `risk ${compactTick(thresholds.cancer_upper)}`, at: "insideBottomRight" as const },
      ]
    : [];
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-1.5">
      <Legend thresholds={thresholds} digits={digits} />
      <div className={`w-full ${heightClass}`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={toRows(groups)} margin={{ top: 8, right: 0, bottom: 4, left: 0 }} barGap={2}>
            <CartesianGrid stroke="var(--hairline)" vertical={false} />
            <XAxis
              dataKey="label"
              interval={0}
              angle={angled ? -25 : 0}
              textAnchor={angled ? "end" : "middle"}
              height={angled ? 58 : 30}
              padding={{ left: 24, right: 0 }}
              tick={AXIS_TEXT}
              tickFormatter={(value: string) => shorten(value, labelChars)}
              stroke="var(--hairline)"
            />
            {(["hq", "risk"] as const).map((axis) => (
              <YAxis
                key={axis}
                yAxisId={axis}
                orientation={axis === "hq" ? "left" : "right"}
                scale="log"
                domain={["auto", "auto"]}
                width={46}
                padding={{ top: 10, bottom: 0 }}
                tick={{ ...AXIS_TEXT, fill: axis === "hq" ? HQ_COLOR : RISK_COLOR }}
                tickFormatter={compactTick}
                stroke="var(--hairline)"
              />
            ))}
            {lines.map((line) => (
              <ReferenceLine
                key={line.y}
                yAxisId={line.axis}
                y={line.y}
                stroke={line.color}
                strokeDasharray="4 3"
                ifOverflow="extendDomain"
                label={{ value: line.text, position: line.at, fill: line.color, fontSize: 10 }}
              />
            ))}
            <Tooltip
              shared={false}
              cursor={{ fill: "var(--hairline)" }}
              content={(props) => <BarTooltip {...props} digits={digits} />}
            />
            <Bar yAxisId="hq" dataKey="hq" name="Hazard quotient" fill={HQ_COLOR} radius={[3, 3, 0, 0]} isAnimationActive={false} />
            <Bar yAxisId="risk" dataKey="risk" name="Lifetime cancer risk" fill={RISK_COLOR} radius={[3, 3, 0, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <BarsAsText groups={groups} digits={digits} caption={caption} />
    </div>
  );
}
