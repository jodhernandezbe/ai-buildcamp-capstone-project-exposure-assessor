import { ChevronRight } from "lucide-react";
import { useId, type ReactNode } from "react";

interface AccordionSectionProps {
  title: string;
  open: boolean;
  onToggle: () => void;
  /** A short state of the content, shown at the heading's right while collapsed or open. */
  summary?: ReactNode;
  children: ReactNode;
}

/** One collapsible section: a heading button that shows or hides its content. */
export function AccordionSection({ title, open, onToggle, summary, children }: AccordionSectionProps) {
  const panelId = useId();
  return (
    <section className="border-t border-hairline first:border-t-0">
      <h3 className="flex items-center gap-3">
        <button
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={onToggle}
          className="spring flex min-w-0 flex-1 items-center gap-2 py-3 text-left text-[15px] font-semibold tracking-tight transition-colors hover:text-accent"
        >
          <ChevronRight
            size={16}
            aria-hidden="true"
            className={`shrink-0 text-fg2 transition-transform duration-300 ${open ? "rotate-90" : ""}`}
          />
          {title}
        </button>
        {summary ? <span className="shrink-0 text-xs text-fg2">{summary}</span> : null}
      </h3>
      <div id={panelId} role="region" aria-label={title} hidden={!open} className="pb-4 pl-6">
        {children}
      </div>
    </section>
  );
}
