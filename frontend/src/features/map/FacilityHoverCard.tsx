import { ChevronRight, X } from "lucide-react";
import { useId, useState, type ReactNode } from "react";

import { StatusPill } from "../../components/ui/StatusPill";
import {
  formatCount,
  formatNumber,
  formatRange,
  formatReported,
  formatWithUnit,
  orNotReported,
} from "../../lib/format";
import type { Extreme, Facility, Screening, Stack } from "../../types/workspace";
import { Metric } from "../overview/Metric";

// More stacks than this start folded: the card stays readable and the risk stays in view.
const STACKS_SHOWN_OPEN = 2;

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

/** Why a facility has no stacks: screened out on the bound, or not assessed (yet). */
function noStacks(screening: Screening | null): string {
  if (screening?.outcome === "screened_out_at_bound") {
    return "None needed: screened out on a conservative bound with a generic stack.";
  }
  return "Not assessed yet: no stack parameters were obtained for this facility.";
}

/** What the screen decided, when it limited or skipped the assessment. */
function ScreeningNote({ screening, digits }: { screening: Screening | null; digits: number }) {
  if (screening === null || screening.outcome === "full") return null;
  if (screening.outcome === "worst_case_only") {
    return (
      <p className="m-0 mt-1 text-xs text-fg2">
        Worst case only, with this facility's own stacks: the weather at the site, the residents and
        the representative case were not computed.
      </p>
    );
  }
  const hq = screening.value_hq !== null ? `HQ ${formatNumber(screening.value_hq, digits)}` : null;
  const risk =
    screening.value_cancer_risk !== null
      ? `cancer risk ${formatNumber(screening.value_cancer_risk, digits)}`
      : null;
  return (
    <div className="mt-1 rounded-lg bg-fg2/5 p-2 text-xs">
      <p className="m-0 font-medium">
        Screened out{screening.outcome === "screened_out_at_bound" ? " on the bound" : " with its own stacks"}
        {hq || risk ? ` (${[hq, risk].filter(Boolean).join(", ")})` : ""}
      </p>
      {screening.reason && <p className="m-0 mt-0.5 text-fg2">{screening.reason}</p>}
    </div>
  );
}

interface SectionProps {
  title: string;
  /** Shown beside the title: a count, or the status pill. */
  aside?: ReactNode;
  initiallyOpen: boolean;
  children: ReactNode;
}

/** A titled part of the card that folds; its heading is the toggle (usable once pinned). */
function Section({ title, aside, initiallyOpen, children }: SectionProps) {
  const [open, setOpen] = useState(initiallyOpen);
  const bodyId = useId();
  return (
    <section className="mt-2">
      <div className="flex items-center justify-between gap-2">
        <h4 className="m-0 text-xs font-semibold uppercase tracking-wide text-fg2">
          <button
            type="button"
            aria-expanded={open}
            aria-controls={bodyId}
            onClick={() => setOpen((value) => !value)}
            className="flex items-center gap-1 rounded uppercase tracking-wide hover:text-fg"
          >
            <ChevronRight
              size={12}
              aria-hidden="true"
              className={`transition-transform duration-200 ${open ? "rotate-90" : ""}`}
            />
            {title}
          </button>
        </h4>
        {aside}
      </div>
      <div id={bodyId} hidden={!open} className="mt-1">
        {children}
      </div>
    </section>
  );
}

interface CardProps {
  facility: Facility;
  digits: number;
  id: string;
  /** A pinned card takes the pointer (its sections fold, it closes by its control). */
  pinned: boolean;
  onClose: () => void;
  /** Tallest the card may be (px), so it scrolls inside the map rather than past it. */
  maxHeight: number;
}

/** The inspector of one facility: identifiers, release, stacks with their tier, and risk. */
export function FacilityHoverCard({ facility, digits, id, pinned, onClose, maxHeight }: CardProps) {
  const { industry, exposure, receptors, stacks, screening } = facility;
  return (
    <div
      id={id}
      role={pinned ? "dialog" : "tooltip"}
      aria-label={pinned ? orNotReported(facility.name) : undefined}
      style={{ maxHeight }}
      className={`glass sheet-in flex w-80 flex-col rounded-2xl text-sm shadow-[var(--shadow)] ${
        pinned ? "pointer-events-auto" : "pointer-events-none"
      }`}
    >
      <header className="flex shrink-0 items-start gap-2 px-3.5 pt-3.5">
        <div className="min-w-0 flex-1">
          <h3 className="m-0 text-base font-semibold">{orNotReported(facility.name)}</h3>
          <p className="m-0 text-xs text-fg2">
            FRS {facility.frs_id} · TRI doc. control no. {orNotReported(facility.doc_ctrl_num)}
          </p>
          <p className="m-0 text-xs text-fg2">
            NAICS {orNotReported(industry?.naics_code)} · {orNotReported(industry?.naics_title)}
          </p>
        </div>
        {pinned ? (
          <button
            type="button"
            aria-label="Close facility details"
            onClick={onClose}
            className="spring -mr-1 -mt-1 grid size-7 shrink-0 place-items-center rounded-full text-fg2 transition hover:bg-hairline hover:text-fg"
          >
            <X size={14} aria-hidden="true" />
          </button>
        ) : (
          <span className="shrink-0 text-[11px] text-fg2">Click to pin</span>
        )}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-3.5 pb-3.5 pt-2">
        <dl className="m-0 grid grid-cols-2 gap-x-3 gap-y-1">
          <Metric label="Reported release">
            {formatReported(facility.total_release)} {facility.release_unit}/yr
          </Metric>
          <Metric label="Emission rate">{formatWithUnit(facility.emission_rate_g_s, "g/s", digits)}</Metric>
          <Metric label="Operating hours">
            {formatReported(facility.operating_hours_per_year)} h/yr
          </Metric>
          <Metric label="CAS number">{orNotReported(facility.cas_number)}</Metric>
        </dl>
        <Section
          title="Stacks"
          aside={<span className="text-xs text-fg2">{stacks.length}</span>}
          initiallyOpen={stacks.length <= STACKS_SHOWN_OPEN}
        >
          {stacks.length === 0 ? (
            <p className="m-0 text-xs text-fg2">{noStacks(screening)}</p>
          ) : (
            <ul className="m-0 grid list-none gap-1.5 p-0">
              {stacks.map((stack, index) => (
                <StackRow key={index} stack={stack} digits={digits} />
              ))}
            </ul>
          )}
        </Section>
        <Section title="Receptor risk" aside={<StatusPill status={facility.status} />} initiallyOpen>
          <ScreeningNote screening={screening} digits={digits} />
          <dl className="m-0 grid grid-cols-2 gap-x-3 gap-y-1">
            <Metric label="Concentration, worst case">
              {exposure?.concentration_worst
                ? `${range(exposure.concentration_worst, digits)} µg/m³`
                : formatNumber(null, digits)}
            </Metric>
            <Metric label="Concentration, representative">
              {exposure?.concentration_representative
                ? `${range(exposure.concentration_representative, digits)} µg/m³`
                : formatNumber(null, digits)}
            </Metric>
            <Metric label="HQ, worst case">{range(exposure?.hq_worst, digits)}</Metric>
            <Metric label="HQ, representative">{range(exposure?.hq_representative, digits)}</Metric>
            <Metric label="Cancer risk, worst case">{range(exposure?.cancer_risk_worst, digits)}</Metric>
            <Metric label="Cancer risk, representative">
              {range(exposure?.cancer_risk_representative, digits)}
            </Metric>
            <Metric label={`Residents within ${receptors ? formatNumber(receptors.radius_km, digits) : "?"} km`}>
              {receptors ? formatCount(receptors.total_population) : formatNumber(null, digits)}
            </Metric>
          </dl>
        </Section>
      </div>
    </div>
  );
}
