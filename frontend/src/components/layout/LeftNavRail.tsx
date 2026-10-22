import {
  LayoutDashboard,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  SquarePen,
} from "lucide-react";
import type { ElementType } from "react";

import { BrandLogo, BrandMark } from "../ui/BrandLogo";

export interface RailRun {
  id: string;
  /** The run's first message; null while it has none. */
  title: string | null;
}

interface LeftNavRailProps {
  collapsed: boolean;
  /** Absent where the rail cannot expand (a narrow window): the toggle is then not shown. */
  onToggle?: (() => void) | undefined;
  runs: RailRun[];
  currentId: string;
  /** False while a turn streams: the conversation cannot be left until it ends. */
  canSwitch: boolean;
  onNewAnalysis: () => void;
  onSelectRun: (id: string) => void;
  /** Return to the workspace: leave fullscreen and close whatever is open over it. */
  onWorkspace: () => void;
  onOpenSettings: () => void;
}

const UNTITLED = "Untitled analysis";

interface ItemProps {
  icon: ElementType;
  label: string;
  collapsed: boolean;
  onClick?: (() => void) | undefined;
  current?: boolean | undefined;
  disabled?: boolean | undefined;
  page?: boolean | undefined;
}

/** One rail entry: icon and label when expanded, the icon alone (named and titled) when collapsed. */
function Item({ icon: Icon, label, collapsed, onClick, current, disabled, page }: ItemProps) {
  return (
    <button
      type="button"
      aria-label={collapsed ? label : undefined}
      title={collapsed ? label : undefined}
      aria-current={page ? "page" : current ? "true" : undefined}
      disabled={disabled}
      onClick={onClick}
      className={`spring relative flex h-9 w-full items-center gap-3 rounded-xl px-[11px] text-left text-sm transition hover:bg-hairline disabled:opacity-40 disabled:hover:bg-transparent ${
        current || page ? "bg-hairline font-semibold" : "text-fg2 hover:text-fg"
      }`}
    >
      {current || page ? (
        <span aria-hidden="true" className="absolute inset-y-2 left-0 w-[3px] rounded-full bg-accent" />
      ) : null}
      <Icon size={18} aria-hidden="true" className="shrink-0" />
      {collapsed ? null : <span className="min-w-0 flex-1 truncate">{label}</span>}
    </button>
  );
}

/** The left rail: brand and toggle, new analysis, the workspace and this session's runs, Settings. */
export function LeftNavRail({
  collapsed,
  onToggle,
  runs,
  currentId,
  canSwitch,
  onNewAnalysis,
  onSelectRun,
  onWorkspace,
  onOpenSettings,
}: LeftNavRailProps) {
  const Toggle = collapsed ? PanelLeftOpen : PanelLeftClose;
  return (
    <div className="flex h-full min-w-0 flex-col gap-1 overflow-hidden bg-surface p-2">
      <div className={`flex ${collapsed ? "flex-col items-center" : "items-center"} gap-1`}>
        {collapsed ? (
          <span role="img" aria-label="EcoFate" title="EcoFate" className="group grid size-9 place-items-center">
            <BrandMark size={32} />
          </span>
        ) : (
          <span className="min-w-0 flex-1 pl-0.5">
            <BrandLogo size={32} label="Exposure & Risk Studio" />
          </span>
        )}
        {onToggle ? (
          <button
            type="button"
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            aria-expanded={!collapsed}
            onClick={onToggle}
            className="spring grid size-9 shrink-0 place-items-center rounded-xl text-fg2 transition hover:bg-hairline hover:text-fg"
          >
            <Toggle size={18} aria-hidden="true" />
          </button>
        ) : null}
      </div>
      <Item
        icon={SquarePen}
        label="New analysis"
        collapsed={collapsed}
        disabled={!canSwitch}
        onClick={onNewAnalysis}
      />
      <div className="mt-2 flex min-h-0 flex-1 flex-col gap-1">
        {collapsed ? null : (
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wider text-fg2">Analysis area</h2>
        )}
        <Item icon={LayoutDashboard} label="Workspace" collapsed={collapsed} onClick={onWorkspace} page />
        <ul aria-label="Runs" className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
          {runs.map((run) => (
            <li key={run.id}>
              <Item
                icon={MessageSquare}
                label={run.title ?? UNTITLED}
                collapsed={collapsed}
                current={run.id === currentId}
                disabled={!canSwitch && run.id !== currentId}
                onClick={() => onSelectRun(run.id)}
              />
            </li>
          ))}
        </ul>
      </div>
      <Item icon={Settings} label="Settings" collapsed={collapsed} onClick={onOpenSettings} />
    </div>
  );
}
