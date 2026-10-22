import { useState, type ReactNode } from "react";
import {
  Group,
  Panel,
  useDefaultLayout,
  usePanelCallbackRef,
} from "react-resizable-panels";

import { safeStorage, type SafeStorage } from "../../lib/safeStorage";
import { usePrefers } from "../../lib/usePrefers";
import type { LayoutConfig } from "../../types/workspace";
import { CopilotToggle } from "./CopilotToggle";
import { PanelFrame } from "./PanelFrame";
import { PanelSplitter } from "./PanelSplitter";
import { useFullscreen } from "./useFullscreen";

export interface RailControls {
  collapsed: boolean;
  /** Absent where the rail cannot expand (the narrow layout). */
  toggle: (() => void) | undefined;
  /** Leaves fullscreen, if a panel is in it. */
  exitFullscreen: () => void;
}

export interface ChatControls {
  collapse: () => void;
}

interface SplitWorkspaceProps {
  /** Layout limits from the server; absent until the settings load (panels are then unbounded). */
  layout: LayoutConfig | undefined;
  /** Viewport width (px) below which the regions stack behind a segmented control. */
  narrowBreakpointPx: number;
  rail: (controls: RailControls) => ReactNode;
  overview: ReactNode;
  map: ReactNode;
  chat: (controls: ChatControls) => ReactNode;
}

type Pane = "overview" | "copilot";
const PANES: { id: Pane; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "copilot", label: "Copilot" },
];

const pct = (share: number): string => `${share * 100}%`;
const SIDE_BY_SIDE = ["rail", "analysis", "chat"];
const STACKED = ["overview", "map"];
const FORGETFUL: SafeStorage = { getItem: () => null, setItem: () => undefined };

function Segments({ pane, onChange }: { pane: Pane; onChange: (pane: Pane) => void }) {
  return (
    <div role="tablist" aria-label="Pane" className="glass m-2 grid grid-cols-2 gap-1 rounded-xl p-1">
      {PANES.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={pane === id}
          onClick={() => onChange(id)}
          className={`spring rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-300 ${
            pane === id ? "bg-accent text-accent-fg" : "text-fg2"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function Narrow({ rail, overview, map, chat }: Omit<SplitWorkspaceProps, "layout" | "narrowBreakpointPx">) {
  const [pane, setPane] = useState<Pane>("overview");
  const { fullscreen, toggle, exit } = useFullscreen();
  const hide = (id: Pane) => (pane !== id ? "hidden" : "");
  return (
    <div className="grid h-dvh w-dvw grid-cols-[auto_minmax(0,1fr)] overflow-hidden">
      <nav aria-label="Navigation" inert={fullscreen !== null} className="border-r border-hairline">
        {rail({ collapsed: true, toggle: undefined, exitFullscreen: exit })}
      </nav>
      <div className="grid min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)]">
        <Segments pane={pane} onChange={setPane} />
        <div className="min-h-0 min-w-0">
          <div className={`grid h-full min-h-0 grid-rows-[minmax(0,2fr)_minmax(0,3fr)] ${hide("overview")}`}>
            <PanelFrame id="overview" title="Overview" fullscreen={fullscreen} onToggle={toggle} scroll>
              {overview}
            </PanelFrame>
            <PanelFrame id="map" title="Map" fullscreen={fullscreen} onToggle={toggle} scroll={false}>
              {map}
            </PanelFrame>
          </div>
          <section aria-label="Copilot" inert={fullscreen !== null} className={`h-full min-h-0 ${hide("copilot")}`}>
            {chat({ collapse: () => setPane("overview") })}
          </section>
        </div>
      </div>
    </div>
  );
}

function limits(layout: LayoutConfig | undefined) {
  if (!layout) return { rail: {}, chat: {}, overview: {} };
  const { rail, chat, overview } = layout;
  return {
    rail: {
      defaultSize: `${rail.default_px}px`,
      minSize: `${rail.min_px}px`,
      maxSize: `${rail.max_px}px`,
      collapsedSize: `${rail.collapsed_px}px`,
    },
    chat: {
      defaultSize: pct(chat.default_share),
      minSize: `${chat.min_px}px`,
      maxSize: pct(chat.max_share),
      collapsedSize: 0,
    },
    overview: {
      defaultSize: pct(overview.default_share),
      minSize: pct(overview.min_share),
      maxSize: pct(overview.max_share),
    },
  };
}

function Wide({ layout, rail, overview, map, chat }: Omit<SplitWorkspaceProps, "narrowBreakpointPx">) {
  // Handles held in state, not refs: the controls handed to the render props read them.
  const [railPanel, setRailPanel] = usePanelCallbackRef();
  const [chatPanel, setChatPanel] = usePanelCallbackRef();
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const { fullscreen, toggle, exit } = useFullscreen();
  const sizes = limits(layout);
  // Sizes are remembered only once the limits are known: the unbounded pre-load layout must
  // not be saved and then restored over the configured defaults.
  const storage = layout ? safeStorage : FORGETFUL;
  const outer = useDefaultLayout({ id: "workspace", panelIds: SIDE_BY_SIDE, storage });
  const inner = useDefaultLayout({ id: "analysis", panelIds: STACKED, storage });
  const inert = fullscreen !== null;
  // While the dock is collapsed, the control that brings it back sits at the top of the overview.
  const showChat = chatCollapsed && !inert ? (
    <CopilotToggle
      open={false}
      onToggle={() => {
        chatPanel?.expand();
        setChatCollapsed(false);
      }}
    />
  ) : null;

  return (
    <div className="h-dvh w-dvw overflow-hidden">
      <Group
        id="workspace"
        orientation="horizontal"
        defaultLayout={outer.defaultLayout}
        onLayoutChanged={outer.onLayoutChanged}
        className="h-full w-full"
      >
        <Panel
          id="rail"
          panelRef={setRailPanel}
          collapsible
          {...sizes.rail}
          onResize={() => setRailCollapsed(railPanel?.isCollapsed() ?? false)}
        >
          <nav aria-label="Navigation" inert={inert} className="h-full min-w-0">
            {rail({
              collapsed: railCollapsed,
              exitFullscreen: exit,
              toggle: () => {
                if (railCollapsed) railPanel?.expand();
                else railPanel?.collapse();
                setRailCollapsed(!railCollapsed);
              },
            })}
          </nav>
        </Panel>
        <PanelSplitter axis="column" label="Resize navigation" />
        <Panel id="analysis" minSize="20%">
          <Group
            id="analysis"
            orientation="vertical"
            defaultLayout={inner.defaultLayout}
            onLayoutChanged={inner.onLayoutChanged}
            className="h-full w-full"
          >
            <Panel id="overview" {...sizes.overview}>
              <PanelFrame
                id="overview"
                title="Overview"
                fullscreen={fullscreen}
                onToggle={toggle}
                scroll
                actions={showChat}
              >
                {overview}
              </PanelFrame>
            </Panel>
            <PanelSplitter axis="row" label="Resize overview and map" />
            <Panel id="map" minSize="15%">
              <PanelFrame id="map" title="Map" fullscreen={fullscreen} onToggle={toggle} scroll={false}>
                {map}
              </PanelFrame>
            </Panel>
          </Group>
        </Panel>
        <PanelSplitter axis="column" label="Resize copilot" />
        <Panel
          id="chat"
          panelRef={setChatPanel}
          collapsible
          {...sizes.chat}
          onResize={() => setChatCollapsed(chatPanel?.isCollapsed() ?? false)}
        >
          <section aria-label="Copilot" inert={inert} className="h-full min-w-0 overflow-hidden">
            {chat({
              collapse: () => {
                chatPanel?.collapse();
                setChatCollapsed(true);
              },
            })}
          </section>
        </Panel>
      </Group>
    </div>
  );
}

/**
 * The full-viewport shell: navigation rail, analysis area (overview above map) and chat dock,
 * separated by draggable splitters. On a narrow viewport the regions stack behind a segmented
 * control. Both layouts keep every region mounted, so no state is lost when switching.
 */
export function SplitWorkspace({ narrowBreakpointPx, ...regions }: SplitWorkspaceProps) {
  const narrow = usePrefers(`(max-width: ${narrowBreakpointPx - 1}px)`);
  // Limits arrive with the settings; the panels are rebuilt once, when they do.
  return narrow ? <Narrow {...regions} /> : <Wide key={regions.layout ? "sized" : "pending"} {...regions} />;
}
