import { TopHeaderBar, type AssistantStatus } from "../../components/layout/TopHeaderBar";
import type { ChatMessage } from "../../hooks/chatState";
import type { Usage } from "../../types/workspace";
import { ChatComposer } from "./ChatComposer";
import { MessageStream } from "./MessageStream";
import { UsageMeter } from "./UsageMeter";

interface ChatDockProps {
  messages: ChatMessage[];
  busy: boolean;
  hasKey: boolean;
  model?: string | undefined;
  suggestions?: string[] | undefined;
  usage: Usage | null;
  onSend: (text: string) => void;
  onNewAssessment: () => void;
  onOpenSettings: () => void;
}

function statusOf(messages: ChatMessage[], busy: boolean): AssistantStatus {
  if (busy) return "thinking";
  const last = messages[messages.length - 1];
  return last?.error ? "error" : "idle";
}

/** The right pane: header, conversation and composer. */
export function ChatDock({
  messages,
  busy,
  hasKey,
  model,
  suggestions,
  usage,
  onSend,
  onNewAssessment,
  onOpenSettings,
}: ChatDockProps) {
  return (
    <div className="flex h-full flex-col">
      <TopHeaderBar
        title="Exposure Assessor"
        subtitle={model}
        status={statusOf(messages, busy)}
        onOpenSettings={onOpenSettings}
      >
        <UsageMeter usage={usage} />
        {messages.length > 0 ? (
          <button
            type="button"
            onClick={onNewAssessment}
            className="spring rounded-full px-3 py-1 text-xs text-accent transition hover:bg-hairline"
          >
            New assessment
          </button>
        ) : null}
      </TopHeaderBar>
      <MessageStream
        messages={messages}
        suggestions={suggestions ?? []}
        canSend={hasKey && !busy}
        onSend={onSend}
      />
      <ChatComposer
        busy={busy}
        hasKey={hasKey}
        onSend={onSend}
        onOpenSettings={onOpenSettings}
      />
    </div>
  );
}
