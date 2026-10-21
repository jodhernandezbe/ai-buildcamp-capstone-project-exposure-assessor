import { useCallback, useEffect, useReducer, useRef } from "react";

import type { WorkspaceState } from "../types/workspace";

import { ApiError, resetThread, streamChat } from "../services/apiClient";
import { chatReducer, initialChatState } from "./chatState";

const newId = (): string => crypto.randomUUID();

function describe(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message;
  return "Something went wrong. Try again.";
}

/** What the conversation tells the rest of the page: the workspace and starting over. */
export interface StreamListeners {
  onWorkspace?: (state: WorkspaceState) => void;
  onReset?: () => void;
}

/** One conversation: send a message, receive the streamed answer, start over. */
export function useAgentStream(listeners: StreamListeners = {}) {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const threadId = useRef(newId());
  const controller = useRef<AbortController | null>(null);
  const heard = useRef(listeners);
  useEffect(() => {
    heard.current = listeners;
  });

  const send = useCallback(async (text: string) => {
    const abort = new AbortController();
    controller.current = abort;
    dispatch({ type: "user_sent", id: newId(), assistantId: newId(), text });
    try {
      for await (const event of streamChat({ thread_id: threadId.current, message: text }, abort.signal)) {
        dispatch({ type: "event", event });
        if (event.type === "workspace_update") heard.current.onWorkspace?.(event.state);
      }
      dispatch({ type: "closed" });
    } catch (error) {
      if (!abort.signal.aborted) dispatch({ type: "failed", message: describe(error) });
    }
  }, []);

  const reset = useCallback(async () => {
    controller.current?.abort();
    const previous = threadId.current;
    threadId.current = newId();
    dispatch({ type: "reset" });
    heard.current.onReset?.();
    try {
      await resetThread(previous);
    } catch {
      // the old thread may still be finishing a turn; the new thread id makes it unreachable
    }
  }, []);

  return { ...state, send, reset };
}
