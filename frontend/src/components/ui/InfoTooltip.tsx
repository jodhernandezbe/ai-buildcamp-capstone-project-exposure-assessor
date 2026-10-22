import { Info } from "lucide-react";
import { useId } from "react";

/** An info icon that explains a field on hover or keyboard focus. */
export function InfoTooltip({ label, text }: { label: string; text: string }) {
  const id = useId();
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-label={label}
        aria-describedby={id}
        className="grid size-5 place-items-center rounded-full text-fg2 transition hover:text-fg"
      >
        <Info size={14} aria-hidden="true" />
      </button>
      <span
        id={id}
        role="tooltip"
        className="glass pointer-events-none absolute left-0 top-full z-50 mt-1 hidden w-64 rounded-xl px-3 py-2 text-xs font-normal leading-snug text-fg shadow-[var(--shadow)] group-focus-within:block group-hover:block"
      >
        {text}
      </span>
    </span>
  );
}
