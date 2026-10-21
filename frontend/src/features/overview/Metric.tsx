import type { ReactNode } from "react";

/** A labelled value of a card: small caption above, tabular figures below. */
export function Metric({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-fg2">{label}</dt>
      <dd className="m-0 text-sm font-medium text-fg tabular-nums">{children}</dd>
    </div>
  );
}

/** Marks values that come from a generic default instead of site-specific data. */
export function ScreeningDefault() {
  return (
    <span className="ml-1.5 rounded-full bg-warn/15 px-1.5 py-0.5 text-[11px] font-medium text-warn">
      screening default
    </span>
  );
}

/** The shell of a ribbon card: a titled glass surface. */
export function CardFrame({
  title,
  children,
  badge,
}: {
  title: string;
  children: ReactNode;
  badge?: ReactNode;
}) {
  return (
    <section
      aria-label={title}
      className="glass flex min-w-0 flex-col gap-2 rounded-2xl p-3.5"
    >
      <header className="flex items-start justify-between gap-2">
        <h2 className="m-0 text-xs font-semibold uppercase tracking-wide text-fg2">{title}</h2>
        {badge}
      </header>
      {children}
    </section>
  );
}
