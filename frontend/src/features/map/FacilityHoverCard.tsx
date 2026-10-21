import { StatusPill } from "../../components/ui/StatusPill";
import {
  formatCount,
  formatNumber,
  formatRange,
  formatReported,
  formatWithUnit,
  orNotReported,
} from "../../lib/format";
import type { Extreme, Facility, Stack } from "../../types/workspace";
import { Metric } from "../overview/Metric";

const range = (extreme: Extreme | null | undefined, digits: number): string =>
  extreme ? formatRange(extreme.low, extreme.high, digits) : formatNumber(null, digits);

function StackRow({ stack, digits }: { stack: Stack; digits: number }) {
  return (
    <li className="rounded-lg bg-fg2/5 p-2">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="rounded-full bg-accent/15 px-2 py-0.5 text-[11px] font-medium text-accent">
          {stack.tier_label ?? "No source reported"}
        </span>
        {stack.stack_number !== null && <span className="text-xs text-fg2">stack {stack.stack_number}</span>}
      </div>
      <dl className="m-0 grid grid-cols-2 gap-x-3 gap-y-1">
        <Metric label="Height">{formatWithUnit(stack.height_m, "m", digits)}</Metric>
        <Metric label="Diameter">{formatWithUnit(stack.diameter_m, "m", digits)}</Metric>
        <Metric label="Exit velocity">{formatWithUnit(stack.exit_velocity_m_s, "m/s", digits)}</Metric>
        <Metric label="Exit temperature">{formatWithUnit(stack.exit_temperature_k, "K", digits)}</Metric>
      </dl>
      {stack.scc && (
        <p className="m-0 mt-1 text-xs text-fg2">
          SCC {stack.scc}
          {stack.scc_description ? ` · ${stack.scc_description}` : ""}
          {stack.scc_score !== null ? ` (score ${formatNumber(stack.scc_score, digits)})` : ""}
        </p>
      )}
    </li>
  );
}

/** The inspector of one facility: identifiers, release, stacks with their tier, and risk. */
export function FacilityHoverCard({ facility, digits, id }: { facility: Facility; digits: number; id: string }) {
  const { industry, exposure, receptors } = facility;
  return (
    <div
      id={id}
      role="tooltip"
      className="glass sheet-in pointer-events-none w-80 rounded-2xl p-3.5 text-sm shadow-[var(--shadow)]"
    >
      <header className="mb-2">
        <h3 className="m-0 text-base font-semibold">{orNotReported(facility.name)}</h3>
        <p className="m-0 text-xs text-fg2">
          FRS {facility.frs_id} · TRI doc. control no. {orNotReported(facility.doc_ctrl_num)}
        </p>
        <p className="m-0 text-xs text-fg2">
          NAICS {orNotReported(industry?.naics_code)} · {orNotReported(industry?.naics_title)}
        </p>
      </header>
      <dl className="m-0 mb-2 grid grid-cols-2 gap-x-3 gap-y-1">
        <Metric label="Reported release">
          {formatReported(facility.total_release)} {facility.release_unit}/yr
        </Metric>
        <Metric label="Emission rate">{formatWithUnit(facility.emission_rate_g_s, "g/s", digits)}</Metric>
        <Metric label="Operating hours">
          {formatReported(facility.operating_hours_per_year)} h/yr
        </Metric>
        <Metric label="CAS number">{orNotReported(facility.cas_number)}</Metric>
      </dl>
      <h4 className="m-0 mb-1 text-xs font-semibold uppercase tracking-wide text-fg2">Stacks</h4>
      {facility.stacks.length === 0 ? (
        <p className="m-0 mb-2 text-xs text-fg2">Stack parameters not reported yet.</p>
      ) : (
        <ul className="m-0 mb-2 grid list-none gap-1.5 p-0">
          {facility.stacks.map((stack, index) => (
            <StackRow key={index} stack={stack} digits={digits} />
          ))}
        </ul>
      )}
      <div className="mb-1 flex items-center justify-between">
        <h4 className="m-0 text-xs font-semibold uppercase tracking-wide text-fg2">Receptor risk</h4>
        <StatusPill status={facility.status} />
      </div>
      <dl className="m-0 grid grid-cols-2 gap-x-3 gap-y-1">
        <Metric label="Concentration, worst case">
          {exposure?.concentration_worst ? `${range(exposure.concentration_worst, digits)} µg/m³` : formatNumber(null, digits)}
        </Metric>
        <Metric label="Concentration, representative">
          {exposure?.concentration_representative
            ? `${range(exposure.concentration_representative, digits)} µg/m³`
            : formatNumber(null, digits)}
        </Metric>
        <Metric label="HQ, worst case">{range(exposure?.hq_worst, digits)}</Metric>
        <Metric label="HQ, representative">{range(exposure?.hq_representative, digits)}</Metric>
        <Metric label="Cancer risk, worst case">{range(exposure?.cancer_risk_worst, digits)}</Metric>
        <Metric label="Cancer risk, representative">{range(exposure?.cancer_risk_representative, digits)}</Metric>
        <Metric label={`Residents within ${receptors ? formatNumber(receptors.radius_km, digits) : "?"} km`}>
          {receptors ? formatCount(receptors.total_population) : formatNumber(null, digits)}
        </Metric>
      </dl>
    </div>
  );
}
