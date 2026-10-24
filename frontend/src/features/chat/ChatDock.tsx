import { TopHeaderBar, type AssistantStatus } from "../../components/layout/TopHeaderBar";
import type { ChatMessage, UsageView } from "../../hooks/chatState";
import { ChatComposer } from "./ChatComposer";
import { ClearChatButton } from "./ClearChatButton";
import { MessageStream } from "./MessageStream";
import { UsageMeter } from "./UsageMeter";

interface ChatDockProps {
  messages: ChatMessage[];
  busy: boolean;
  hasKey: boolean;
  model?: string | undefined;
  suggestions?: string[] | undefined;
  usage: UsageView | null;
  /** A message about switching runs (for example, that one is no longer available). */
  notice?: string | null | undefined;
  onSend: (text: string) => void;
  onClear: () => void;
  onOpenSettings: () => void;
  onCollapse: () => void;
}

function statusOf(messages: ChatMessage[], busy: boolean): AssistantStatus {
  if (busy) return "thinking";
  const last = messages[messages.length - 1];
  return last?.error ? "error" : "idle";
}

/** The chat dock: header, conversation and composer. */
export function ChatDock({
  messages,
  busy,
  hasKey,
  model,
  suggestions,
  usage,
  notice,
  onSend,
  onClear,
  onOpenSettings,
  onCollapse,
}: ChatDockProps) {
  return (
    <div className="flex h-full flex-col">
      <TopHeaderBar
        title="EcoFate"
        subtitle={model}
        status={statusOf(messages, busy)}
        onCollapse={onCollapse}
      >
        <UsageMeter usage={usage} />
        <ClearChatButton disabled={busy || messages.length === 0} onClear={onClear} />
      </TopHeaderBar>
      <MessageStream
        messages={messages}
        suggestions={suggestions ?? []}
        canSend={hasKey && !busy}
        onSend={onSend}
      />
      {notice ? (
        <p role="status" className="px-5 pb-1 text-center text-xs text-fg2">
          {notice}
        </p>
      ) : null}
      <ChatComposer
        busy={busy}
        hasKey={hasKey}
        onSend={onSend}
        onOpenSettings={onOpenSettings}
      />
    </div>
  );
}
