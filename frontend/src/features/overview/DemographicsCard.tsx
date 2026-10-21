import { SegmentedBar } from "../../components/ui/SegmentedBar";
import { formatCount, formatNumber, orNotReported } from "../../lib/format";
import type { Receptors } from "../../types/workspace";
import { CardFrame, Metric, ScreeningDefault } from "./Metric";

const BANDS = ["0-4", "5-17", "18-64", "65+"];

/** Residents within the buffer radius and the share of each age band. */
export function DemographicsCard({ receptors, digits }: { receptors: Receptors | null; digits: number }) {
  if (!receptors) {
    return (
      <CardFrame title="Exposed population">
        <p className="m-0 text-sm text-fg2">Population not reported yet.</p>
      </CardFrame>
    );
  }
  const segments = BANDS.map((band) => ({ label: band, value: receptors.age_distribution[band] ?? 0 }));
  return (
    <CardFrame title="Exposed population">
      <dl className="m-0 grid grid-cols-2 gap-2">
        <Metric label="Residents">{formatCount(receptors.total_population)}</Metric>
        <Metric label="Within radius">{formatNumber(receptors.radius_km, digits)} km</Metric>
      </dl>
      <SegmentedBar segments={segments} format={(v) => `${formatNumber(v, digits)}%`} />
      <p className="m-0 text-xs text-fg2">
        {orNotReported(receptors.source)}
        {receptors.screening_default && <ScreeningDefault />}
      </p>
    </CardFrame>
  );
}
