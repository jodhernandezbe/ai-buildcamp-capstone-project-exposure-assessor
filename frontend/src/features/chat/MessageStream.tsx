import { useEffect, useRef } from "react";
import Markdown from "react-markdown";

import type { ChatMessage } from "../../hooks/chatState";
import { SuggestionChips } from "./SuggestionChips";
import { ToolExecutionPills } from "./ToolExecutionPill";

function Assistant({ message }: { message: ChatMessage }) {
  return (
    <div className="max-w-[92%] text-[15px] leading-relaxed">
      <ToolExecutionPills steps={message.tools} />
      {message.text ? (
        <div className="[&_a]:text-accent [&_a]:underline [&_code]:rounded [&_code]:bg-hairline [&_code]:px-1 [&_ol]:ml-5 [&_ol]:list-decimal [&_p]:my-2 [&_table]:my-2 [&_td]:border [&_td]:border-hairline [&_td]:px-2 [&_th]:border [&_th]:border-hairline [&_th]:px-2 [&_ul]:ml-5 [&_ul]:list-disc">
          <Markdown
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {message.text}
          </Markdown>
        </div>
      ) : message.streaming && !message.error ? (
        <span className="text-fg2" aria-live="polite">
          Thinking…
        </span>
      ) : null}
      {message.error ? (
        <p role="alert" className="mt-2 rounded-xl border border-hairline px-3 py-2 text-sm text-bad">
          {message.error}
        </p>
      ) : null}
    </div>
  );
}

function User({ message }: { message: ChatMessage }) {
  return (
    <div className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl bg-accent px-4 py-2 text-[15px] text-accent-fg">
      {message.text}
    </div>
  );
}

interface MessageStreamProps {
  messages: ChatMessage[];
  suggestions?: string[];
  canSend?: boolean;
  onSend?: (text: string) => void;
}

export function MessageStream({
  messages,
  suggestions = [],
  canSend = false,
  onSend,
}: MessageStreamProps) {
  const end = useRef<HTMLDivElement>(null);
  const last = messages[messages.length - 1];
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end" });
  }, [messages.length, last?.text]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4" aria-label="Conversation">
      {messages.length === 0 ? (
        <div className="mt-10">
          <p className="text-center text-sm text-fg2">
            Ask about a chemical, its releases or its exposure.
          </p>
          <SuggestionChips
            suggestions={suggestions}
            disabled={!canSend}
            onPick={(text) => onSend?.(text)}
          />
        </div>
      ) : (
        <ol className="flex flex-col gap-4">
          {messages.map((message) => (
            <li key={message.id} className="flex">
              {message.role === "user" ? <User message={message} /> : <Assistant message={message} />}
            </li>
          ))}
        </ol>
      )}
      <div ref={end} />
    </div>
  );
}
