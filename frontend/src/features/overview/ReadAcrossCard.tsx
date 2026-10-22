import { formatNumber, formatWithUnit, orNotReported } from "../../lib/format";
import type { Chemical, ReadAcross } from "../../types/workspace";
import { CardFrame, Metric } from "./Metric";

const BADGES: Record<ReadAcross["kind"], { label: string; tone: string }> = {
  direct_tri_match: { label: "Direct TRI match", tone: "bg-ok/15 text-ok" },
  read_across: { label: "Read-across surrogate", tone: "bg-accent/15 text-accent" },
  unresolved: { label: "Unresolved", tone: "bg-bad/15 text-bad" },
  not_evaluated: { label: "Not evaluated", tone: "bg-fg2/10 text-fg2" },
};

function Badge({ kind }: { kind: ReadAcross["kind"] }) {
  const { label, tone } = BADGES[kind];
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}>{label}</span>;
}

function Surrogate({ match, digits }: { match: ReadAcross; digits: number }) {
  const inDomain = match.within_applicability_domain === true;
  return (
    <div className="rounded-xl bg-fg2/5 p-2.5 text-sm">
      <p className="m-0 font-medium">
        {orNotReported(match.surrogate_name)} <span className="text-fg2">({orNotReported(match.surrogate_cas)})</span>
      </p>
      <dl className="m-0 mt-1.5 grid grid-cols-3 gap-2">
        <Metric label="Hybrid score">{formatNumber(match.hybrid_score, digits)}</Metric>
        <Metric label="Cosine (MolDeBERTa)">{formatNumber(match.cosine_similarity, digits)}</Metric>
        <Metric label="Tanimoto (ECFP4)">{formatNumber(match.tanimoto_similarity, digits)}</Metric>
      </dl>
      <p className={`m-0 mt-1.5 text-xs font-medium ${inDomain ? "text-ok" : "text-bad"}`}>
        {inDomain ? "Within applicability domain" : "Outside applicability domain"}
      </p>
    </div>
  );
}

/** The chemical, its benchmarks with their sources, and how it relates to the TRI list. */
export function ReadAcrossCard({ chemical, digits }: { chemical: Chemical; digits: number }) {
  const { read_across: match, sources } = chemical;
  return (
    <CardFrame title="Chemical & provenance" badge={<Badge kind={match.kind} />}>
      {chemical.name !== null && (
        <p className="m-0 mb-1.5 text-sm font-medium" data-testid="chemical-name">
          {chemical.name}
        </p>
      )}
      <dl className="m-0 grid grid-cols-2 gap-2">
        <Metric label="CAS number">{orNotReported(chemical.cas_number)}</Metric>
        <Metric label="Molecular weight">
          {formatWithUnit(chemical.molecular_weight_g_mol, "g/mol", digits)}
        </Metric>
        <Metric label={`Inhalation RfC${sources.rfc ? ` · ${sources.rfc}` : ""}`}>
          {formatWithUnit(chemical.rfc_mg_m3, "mg/m³", digits)}
        </Metric>
        <Metric label={`Inhalation unit risk${sources.iur ? ` · ${sources.iur}` : ""}`}>
          {formatWithUnit(chemical.iur_per_ug_m3, "(µg/m³)⁻¹", digits)}
        </Metric>
      </dl>
      {match.kind === "read_across" && <Surrogate match={match} digits={digits} />}
    </CardFrame>
  );
}
