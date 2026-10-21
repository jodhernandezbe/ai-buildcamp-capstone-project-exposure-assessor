import { Settings } from "lucide-react";
import type { ReactNode } from "react";

export type AssistantStatus = "idle" | "thinking" | "error";

const STATUS: Record<AssistantStatus, { label: string; dot: string }> = {
  idle: { label: "Ready", dot: "bg-ok" },
  thinking: { label: "Thinking", dot: "bg-warn animate-pulse" },
  error: { label: "Needs attention", dot: "bg-bad" },
};

interface TopHeaderBarProps {
  title: string;
  subtitle?: string | undefined;
  status: AssistantStatus;
  onOpenSettings: () => void;
  children?: ReactNode;
}

/** Assistant title, live status and the gear button at the top right. */
export function TopHeaderBar({
  title,
  subtitle,
  status,
  onOpenSettings,
  children,
}: TopHeaderBarProps) {
  const { label, dot } = STATUS[status];
  return (
    <header className="glass flex items-center gap-3 border-x-0 border-t-0 px-5 py-3">
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-[15px] font-semibold tracking-tight">{title}</h1>
        <p className="flex items-center gap-1.5 text-xs text-fg2" role="status">
          <span aria-hidden="true" className={`inline-block size-2 rounded-full ${dot}`} />
          {label}
          {subtitle ? <span aria-hidden="true">· {subtitle}</span> : null}
        </p>
      </div>
      {children}
      <button
        type="button"
        aria-label="Settings"
        onClick={onOpenSettings}
        className="spring grid size-9 place-items-center rounded-full text-fg2 transition hover:bg-hairline hover:text-fg"
      >
        <Settings size={18} aria-hidden="true" />
      </button>
    </header>
  );
}
