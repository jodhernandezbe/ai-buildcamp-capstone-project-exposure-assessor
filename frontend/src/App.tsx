import { useState } from "react";

import { SplitWorkspace } from "./components/layout/SplitWorkspace";
import { ChatDock } from "./features/chat/ChatDock";
import { OverviewPane } from "./features/overview/OverviewPane";
import { ApiKeyVaultModal } from "./features/settings/ApiKeyVaultModal";
import { useAgentStream } from "./hooks/useAgentStream";
import { useClientConfig } from "./hooks/useClientConfig";
import { useKeyStatus } from "./hooks/useKeyStatus";
import { useWorkspaceStore } from "./hooks/useWorkspaceStore";

// Until the server sends its display settings the ribbon shows these many digits.
const DEFAULT_DIGITS = 2;
const DEFAULT_BREAKPOINT_PX = 900;

export function App() {
  const store = useWorkspaceStore();
  const chat = useAgentStream({ onWorkspace: store.apply, onReset: store.clear });
  const key = useKeyStatus();
  const config = useClientConfig();
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <>
      <SplitWorkspace
        narrowBreakpointPx={config?.narrow_breakpoint_px ?? DEFAULT_BREAKPOINT_PX}
        left={
          <OverviewPane
            workspace={store.workspace}
            digits={config?.significant_digits ?? DEFAULT_DIGITS}
            map={config?.map}
          />
        }
        right={
          <ChatDock
            messages={chat.messages}
            busy={chat.busy}
            hasKey={key.statuses?.openai.configured === true}
            model={config?.model}
            suggestions={config?.suggestions}
            usage={chat.usage}
            onSend={(text) => void chat.send(text)}
            onNewAssessment={() => void chat.reset()}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        }
      />
      <ApiKeyVaultModal
        open={settingsOpen}
        statuses={key.statuses}
        busy={key.busy}
        error={key.error}
        onSave={key.save}
        onClear={key.clear}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
}
