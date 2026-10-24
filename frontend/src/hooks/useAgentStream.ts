import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import type {
  ChatRequest,
  ConfirmationAnswers,
  ConfirmationPrompt,
  WorkspaceState,
} from "../types/workspace";

import { ApiError, getThread, streamChat } from "../services/apiClient";
import { chatReducer, initialChatState } from "./chatState";

const newId = (): string => crypto.randomUUID();
const NOT_FOUND = 404;
const UNPROCESSABLE = 422;

function describe(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message;
  return "Something went wrong. Try again.";
}

/** What the conversation tells the rest of the page. */
export interface StreamListeners {
  /** The id of the run the page opens on (generated here when absent). */
  firstThreadId?: string;
  /** A workspace update streamed in the current run. */
  onWorkspace?: (state: WorkspaceState) => void;
  /** The workspace replaced as a whole: a new run (empty) or a restored one. */
  onReplace?: (state: WorkspaceState | null) => void;
  /** A new, empty run was started. */
  onNewRun?: (threadId: string) => void;
  /** The user sent a message in a run. */
  onSent?: (threadId: string, text: string) => void;
  /** A run the server no longer holds was selected. */
  onGone?: (threadId: string) => void;
}

/** One conversation at a time: send a message, receive the streamed answer, switch runs. */
export function useAgentStream(listeners: StreamListeners = {}) {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const [threadId, setThreadId] = useState(() => listeners.firstThreadId ?? newId());
  const [notice, setNotice] = useState<string | null>(null);
  const current = useRef(threadId);
  const busy = useRef(false);
  const heard = useRef(listeners);
  const empty = useRef(true);
  useEffect(() => {
    heard.current = listeners;
    busy.current = state.busy;
    empty.current = state.messages.length === 0;
  });

  /** Stream one turn: a message, or the user's answers to the open request. */
  const turn = useCallback(
    async (body: ChatRequest, shown: string, reopen: ConfirmationPrompt | null) => {
      const abort = new AbortController();
      const thread = current.current;
      setNotice(null);
      dispatch({ type: "user_sent", id: newId(), assistantId: newId(), text: shown });
      heard.current.onSent?.(thread, shown);
      try {
        for await (const event of streamChat(body, abort.signal)) {
          dispatch({ type: "event", event });
          if (event.type === "workspace_update") heard.current.onWorkspace?.(event.state);
        }
        dispatch({ type: "closed" });
      } catch (error) {
        // A value the server refuses leaves the request open: show it again to correct.
        if (reopen && error instanceof ApiError && error.status === UNPROCESSABLE) {
          dispatch({ type: "rejected", prompt: reopen });
          setNotice(describe(error));
          return;
        }
        dispatch({ type: "failed", message: describe(error) });
      }
    },
    [],
  );

  const send = useCallback(
    (text: string) => turn({ thread_id: current.current, message: text }, text, null),
    [turn],
  );

  /** Send the user's answers to the open request; a rejected reply leaves the request open. */
  const answer = useCallback(
    (answers: ConfirmationAnswers, shown: string, prompt: ConfirmationPrompt) =>
      turn({ thread_id: current.current, answers }, shown, prompt),
    [turn],
  );

  /**
   * Start an empty run; the previous run stays on the server for the rail to list. A run that
   * has no messages yet is already that: nothing is started twice.
   */
  const newRun = useCallback(() => {
    if (busy.current || empty.current) return;
    const id = newId();
    current.current = id;
    setThreadId(id);
    setNotice(null);
    dispatch({ type: "reset" });
    heard.current.onReplace?.(null);
    heard.current.onNewRun?.(id);
  }, []);

  /** Bring back a held run's messages and workspace and continue that conversation. */
  const selectRun = useCallback(async (id: string) => {
    if (busy.current || id === current.current) return;
    try {
      const snapshot = await getThread(id);
      const ids = snapshot.messages.map(() => newId());
      current.current = id;
      setThreadId(id);
      setNotice(null);
      dispatch({ type: "restore", snapshot, ids });
      heard.current.onReplace?.(snapshot.workspace);
    } catch (error) {
      if (error instanceof ApiError && error.status === NOT_FOUND) {
        heard.current.onGone?.(id);
        setNotice("That run is no longer available.");
      } else {
        setNotice(describe(error));
      }
    }
  }, []);

  return { ...state, threadId, notice, send, answer, newRun, selectRun };
}
