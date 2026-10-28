import { SegmentedBar } from "../../components/ui/SegmentedBar";
import { formatCount, formatNumber, orNotReported } from "../../lib/format";
import type { Dose, Receptors } from "../../types/workspace";
import { CardFrame, Metric, ScreeningDefault } from "./Metric";

const BANDS = ["0-4", "5-17", "18-64", "65+"];

/** Inhalation dose of each age band that has residents, the most exposed band marked. */
function DoseList({ dose, digits }: { dose: Dose; digits: number }) {
  return (
    <div>
      <h3 className="m-0 text-xs text-fg2">Inhalation dose, worst case (mg/(kg·day))</h3>
      <dl className="m-0 mt-1 grid grid-cols-2 gap-x-3 gap-y-1">
        {Object.entries(dose.by_band).map(([band, value]) => (
          <Metric key={band} label={band === dose.highest_band ? `Age ${band} (highest)` : `Age ${band}`}>
            {formatNumber(value, digits)}
          </Metric>
        ))}
      </dl>
    </div>
  );
}

/** Residents within the buffer radius, the share of each age band and the dose they receive. */
export function DemographicsCard({
  receptors,
  dose,
  digits,
}: {
  receptors: Receptors | null;
  dose: Dose | null;
  digits: number;
}) {
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
      {dose && Object.keys(dose.by_band).length > 0 && <DoseList dose={dose} digits={digits} />}
      <p className="m-0 text-xs text-fg2">
        {orNotReported(receptors.source)}
        {receptors.screening_default && <ScreeningDefault />}
      </p>
    </CardFrame>
  );
}
