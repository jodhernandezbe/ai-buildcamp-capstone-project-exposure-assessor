import { useState } from "react";

import { LeftNavRail } from "./components/layout/LeftNavRail";
import { SplitWorkspace } from "./components/layout/SplitWorkspace";
import { ChatDock } from "./features/chat/ChatDock";
import { MapPanel } from "./features/map/MapPanel";
import { OverviewPanel } from "./features/overview/OverviewPanel";
import { SettingsDrawer } from "./features/settings/SettingsDrawer";
import { useAgentStream } from "./hooks/useAgentStream";
import { useClientConfig } from "./hooks/useClientConfig";
import { useKeyStatus } from "./hooks/useKeyStatus";
import { useRunHistory } from "./hooks/useRunHistory";
import { useWorkspaceStore } from "./hooks/useWorkspaceStore";

// Until the server sends its display settings the ribbon shows these many digits.
const DEFAULT_DIGITS = 2;
const DEFAULT_BREAKPOINT_PX = 900;

export function App() {
  const store = useWorkspaceStore();
  const [firstRun] = useState(() => crypto.randomUUID());
  const history = useRunHistory(firstRun);
  const chat = useAgentStream({
    firstThreadId: firstRun,
    onWorkspace: store.apply,
    onReplace: (state) => (state ? store.replace(state) : store.clear()),
    onNewRun: history.add,
    onSent: history.title,
    onGone: history.remove,
  });
  const key = useKeyStatus();
  const config = useClientConfig();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const digits = config?.significant_digits ?? DEFAULT_DIGITS;

  return (
    <>
      <SplitWorkspace
        layout={config?.layout}
        narrowBreakpointPx={config?.narrow_breakpoint_px ?? DEFAULT_BREAKPOINT_PX}
        rail={({ collapsed, toggle, exitFullscreen }) => (
          <LeftNavRail
            collapsed={collapsed}
            onToggle={toggle}
            runs={history.runs}
            currentId={chat.threadId}
            canSwitch={!chat.busy}
            onNewAnalysis={chat.newRun}
            onSelectRun={(id) => void chat.selectRun(id)}
            onWorkspace={() => {
              setSettingsOpen(false);
              exitFullscreen();
            }}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        )}
        overview={<OverviewPanel workspace={store.workspace} digits={digits} thresholds={config?.thresholds} />}
        map={<MapPanel workspace={store.workspace} viewEpoch={store.epoch} digits={digits} map={config?.map} />}
        chat={({ collapse }) => (
          <ChatDock
            messages={chat.messages}
            busy={chat.busy}
            hasKey={key.statuses?.openai.configured === true}
            model={config?.model}
            suggestions={config?.suggestions}
            usage={chat.usage}
            notice={chat.notice}
            onSend={(text) => void chat.send(text)}
            onOpenSettings={() => setSettingsOpen(true)}
            onCollapse={collapse}
          />
        )}
      />
      <SettingsDrawer
        open={settingsOpen}
        statuses={key.statuses}
        busy={key.busy}
        outcomes={key.outcomes}
        loadError={key.loadError}
        onSave={key.save}
        onClear={key.clear}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
}
