import { TierPill } from "../../components/ui/TierPill";
import {
  formatNumber,
  formatSchedule,
  formatWithUnit,
  NOT_REPORTED,
  orNotReported,
} from "../../lib/format";
import type { Facility, VentilationTier } from "../../types/workspace";
import { Metric } from "../overview/Metric";

function TierRow({ tier, digits }: { tier: VentilationTier; digits: number }) {
  return (
    <section aria-label={tier.label} className="rounded-lg bg-fg2/5 p-2">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h5 className="m-0 text-xs font-semibold">{tier.label}</h5>
        <TierPill tier={tier.risk_tier} />
      </div>
      <dl className="m-0 grid grid-cols-2 gap-x-3 gap-y-1">
        <Metric label="8-hr TWA">{formatWithUnit(tier.twa_mg_m3, "mg/m³", digits)}</Metric>
        <Metric label="TWA / limit (R_OEL)">{formatNumber(tier.oel_ratio, digits)}</Metric>
        <Metric label="Worker HQ">{formatNumber(tier.hq, digits)}</Metric>
        <Metric label="Worker cancer risk">{formatNumber(tier.cancer_risk, digits)}</Metric>
      </dl>
    </section>
  );
}

/** The worker (box model) screening of one facility: the same kind of detail as the receptor risk. */
export function WorkerSection({ facility, digits }: { facility: Facility; digits: number }) {
  const { occupational_exposure: worker, operational_profile: profile } = facility;
  const sector = profile?.cdr_sector;
  return (
    <>
      <p className="m-0 mb-1 text-xs text-fg2">
        Operating schedule: {formatSchedule(profile)}
        {sector ? ` · CDR ${sector.code}, ${sector.name}` : ""}
      </p>
      {worker === null ? (
        <p className="m-0 text-xs text-fg2">Worker exposure: {NOT_REPORTED}.</p>
      ) : (
        <>
          <dl className="m-0 mb-1 grid grid-cols-2 gap-x-3 gap-y-1">
            <Metric label="Fugitive release">
              {formatWithUnit(worker.fugitive_release_kg_per_year, "kg/yr", digits)}
            </Metric>
            <Metric label="Occupational limit (TWA)">
              {formatWithUnit(worker.oel_twa_mg_m3, "mg/m³", digits)}
            </Metric>
            <Metric label="Limit source">{orNotReported(worker.oel_source)}</Metric>
            <Metric label={`Vapor pressure (context)${worker.vapor_pressure_source ? ` · ${worker.vapor_pressure_source}` : ""}`}>
              {formatWithUnit(worker.vapor_pressure_mmhg, "mmHg", digits)}
            </Metric>
          </dl>
          <div className="grid gap-1.5">
            <TierRow tier={worker.baseline} digits={digits} />
            <TierRow tier={worker.worst_case} digits={digits} />
          </div>
          {worker.warnings.length > 0 && (
            <ul className="m-0 mt-1 grid list-none gap-0.5 p-0 text-xs text-fg2">
              {worker.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
        </>
      )}
    </>
  );
}
