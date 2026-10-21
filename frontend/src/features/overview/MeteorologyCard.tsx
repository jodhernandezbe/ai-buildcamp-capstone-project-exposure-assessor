import { Navigation } from "lucide-react";

import { formatNumber, formatWithUnit, orNotReported } from "../../lib/format";
import type { Meteorology } from "../../types/workspace";
import { CardFrame, Metric, ScreeningDefault } from "./Metric";

/** Where the weather is for: the facility at that point, else the point itself. */
function place(weather: Meteorology): string {
  if (weather.frs_id) return `For ${weather.facility_name ?? `FRS ${weather.frs_id}`}`;
  const lat = weather.latitude.toFixed(3);
  const lon = weather.longitude.toFixed(3);
  return `At ${lat}, ${lon} (not one of the facilities)`;
}

/** Wind, temperature and stability; the arrow points where the wind blows to. */
export function MeteorologyCard({ weather, digits }: { weather: Meteorology | null; digits: number }) {
  if (!weather) {
    return (
      <CardFrame title="Meteorology">
        <p className="m-0 text-sm text-fg2">Weather not reported yet.</p>
      </CardFrame>
    );
  }
  return (
    <CardFrame title="Meteorology">
      <div className="flex items-center gap-3">
        <Navigation
          aria-hidden
          className="spring size-8 shrink-0 text-accent transition-transform duration-500"
          style={{ transform: `rotate(${weather.wind_toward_deg}deg)` }}
        />
        <dl className="m-0 grid flex-1 grid-cols-2 gap-2">
          <Metric label="Wind speed">{formatWithUnit(weather.wind_speed_m_s, "m/s", digits)}</Metric>
          <Metric label="Blowing from">{formatNumber(weather.wind_from_deg, digits)}°</Metric>
          <Metric label="Temperature">{formatWithUnit(weather.ambient_temperature_k, "K", digits)}</Metric>
          <Metric label="Stability class">{orNotReported(weather.stability_class)}</Metric>
        </dl>
      </div>
      <p className="m-0 truncate text-xs font-medium text-fg">{place(weather)}</p>
      <p className="m-0 text-xs text-fg2">
        {orNotReported(weather.source)}
        {weather.screening_default && <ScreeningDefault />}
      </p>
    </CardFrame>
  );
}
