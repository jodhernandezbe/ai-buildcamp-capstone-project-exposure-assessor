export interface Segment {
  label: string;
  value: number;
}

const SHADES = ["bg-accent", "bg-accent/75", "bg-accent/50", "bg-accent/30"];

/** A horizontal stacked bar of shares that add up to 100, with a legend of the bands. */
export function SegmentedBar({ segments, format }: { segments: Segment[]; format: (v: number) => string }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  return (
    <div>
      <div
        role="img"
        aria-label={segments.map((s) => `${s.label}: ${format(s.value)}`).join(", ")}
        className="flex h-2.5 overflow-hidden rounded-full bg-fg2/10"
      >
        {segments.map((s, i) => (
          <div
            key={s.label}
            className={`${SHADES[i % SHADES.length]} spring transition-[width] duration-500`}
            style={{ width: `${total > 0 ? (s.value / total) * 100 : 0}%` }}
          />
        ))}
      </div>
      <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-fg2">
        {segments.map((s, i) => (
          <li key={s.label} className="flex items-center gap-1">
            <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${SHADES[i % SHADES.length]}`} />
            {s.label} <span className="text-fg">{format(s.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
