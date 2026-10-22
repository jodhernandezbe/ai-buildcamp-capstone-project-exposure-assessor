import { Maximize2, Minimize2 } from "lucide-react";
import type { ReactNode } from "react";

interface PanelHeaderProps {
  title: string;
  fullscreen: boolean;
  onToggleFullscreen: () => void;
  /** Extra controls after the fullscreen toggle, at the panel's outer edge. */
  children?: ReactNode;
}

/** A panel's title bar with its fullscreen toggle (then any extra controls) at the top right. */
export function PanelHeader({ title, fullscreen, onToggleFullscreen, children }: PanelHeaderProps) {
  const Icon = fullscreen ? Minimize2 : Maximize2;
  return (
    <header className="flex shrink-0 items-center gap-2 border-b border-hairline px-4 py-2">
      <h2 className="min-w-0 flex-1 truncate text-xs font-semibold uppercase tracking-wider text-fg2">
        {title}
      </h2>
      <button
        type="button"
        aria-label={fullscreen ? "Exit fullscreen" : "Enter fullscreen"}
        aria-pressed={fullscreen}
        onClick={onToggleFullscreen}
        className="spring grid size-7 place-items-center rounded-full text-fg2 transition hover:bg-hairline hover:text-fg"
      >
        <Icon size={15} aria-hidden="true" />
      </button>
      {children}
    </header>
  );
}
