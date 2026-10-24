import type { ConfirmationPrompt, StreamEvent, ThreadSnapshot, UsageTotals } from "../types/workspace";

export interface ToolStep {
  callId: string;
  label: string;
  state: "running" | "done" | "error";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  error: string | null;
  streaming: boolean;
  tools: ToolStep[];
}

/** What the usage meter shows: the session, and the last turn when one was streamed here. */
export interface UsageView {
  turn: UsageTotals | null;
  session: UsageTotals;
}

export interface ChatState {
  messages: ChatMessage[];
  busy: boolean;
  usage: UsageView | null;
  /** The open request for missing values the user must answer, if the turn stopped for one. */
  confirmation: ConfirmationPrompt | null;
}

export type ChatAction =
  | { type: "user_sent"; id: string; assistantId: string; text: string }
  | { type: "event"; event: StreamEvent }
  | { type: "failed"; message: string }
  | { type: "closed" }
  | { type: "rejected"; prompt: ConfirmationPrompt | null }
  | { type: "restore"; snapshot: ThreadSnapshot; ids: string[] }
  | { type: "reset" };

export const initialChatState: ChatState = {
  messages: [],
  busy: false,
  usage: null,
  confirmation: null,
};

function updateLastAssistant(
  state: ChatState,
  change: (message: ChatMessage) => ChatMessage,
): ChatState {
  const index = state.messages.findLastIndex((message) => message.role === "assistant");
  const target = state.messages[index];
  if (!target) return state;
  const messages = [...state.messages];
  messages[index] = change(target);
  return { ...state, messages };
}

type ToolEvent = Extract<StreamEvent, { type: "tool_status" }>;

function withToolStatus(message: ChatMessage, event: ToolEvent): ChatMessage {
  if (event.phase === "started") {
    if (message.tools.some((step) => step.callId === event.call_id)) return message;
    const text = message.text && !message.text.endsWith("\n\n") ? message.text + "\n\n" : message.text;
    const step: ToolStep = { callId: event.call_id, label: event.label, state: "running" };
    return { ...message, text, tools: [...message.tools, step] };
  }
  const state: ToolStep["state"] = event.status === "error" ? "error" : "done";
  const known = message.tools.some((step) => step.callId === event.call_id);
  const tools = known
    ? message.tools.map((step) => (step.callId === event.call_id ? { ...step, state } : step))
    : [...message.tools, { callId: event.call_id, label: event.label, state }];
  return { ...message, tools };
}

function onEvent(state: ChatState, event: StreamEvent): ChatState {
  switch (event.type) {
    case "token":
      return updateLastAssistant(state, (m) => ({ ...m, text: m.text + event.text }));
    case "assistant_message":
      // Streamed tokens already carry the text; this fills in for a model that did not stream.
      return updateLastAssistant(state, (m) => (m.text ? m : { ...m, text: event.text }));
    case "guardrail_pivot":
      // An off-topic turn is answered like any other: the redirect is the assistant's message.
      return updateLastAssistant(state, (m) => (m.text ? m : { ...m, text: event.text }));
    case "tool_status":
      return updateLastAssistant(state, (m) => withToolStatus(m, event));
    case "confirmation_request":
      return {
        ...state,
        confirmation: { request_id: event.request_id, entries: event.entries },
      };
    case "usage":
      return { ...state, usage: { turn: event.turn, session: event.session } };
    case "error":
      return updateLastAssistant(state, (m) => ({ ...m, error: event.message }));
    case "turn_finished":
      return { ...updateLastAssistant(state, (m) => ({ ...m, streaming: false })), busy: false };
    default:
      return state;
  }
}

/** A held thread's text messages and session usage; its tool steps are not stored. */
function restored(snapshot: ThreadSnapshot, ids: string[]): ChatState {
  const messages = snapshot.messages.map((message, index): ChatMessage => ({
    id: ids[index] ?? `restored-${index}`,
    role: message.role,
    text: message.text,
    error: null,
    streaming: false,
    tools: [],
  }));
  const usage = snapshot.usage.calls > 0 ? { turn: null, session: snapshot.usage } : null;
  return { messages, busy: false, usage, confirmation: snapshot.confirmation ?? null };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "user_sent":
      return {
        ...state,
        busy: true,
        confirmation: null,
        messages: [
          ...state.messages,
          {
            id: action.id,
            role: "user",
            text: action.text,
            error: null,
            streaming: false,
            tools: [],
          },
          {
            id: action.assistantId,
            role: "assistant",
            text: "",
            error: null,
            streaming: true,
            tools: [],
          },
        ],
      };
    case "event":
      return onEvent(state, action.event);
    case "failed":
      return {
        ...updateLastAssistant(state, (m) => ({ ...m, error: action.message, streaming: false })),
        busy: false,
      };
    case "closed":
      return { ...updateLastAssistant(state, (m) => ({ ...m, streaming: false })), busy: false };
    case "rejected":
      // The server refused the reply and recorded nothing: take back the optimistic turn and
      // show the same request again so the user can correct the answer.
      return {
        ...state,
        messages: state.messages.slice(0, -2),
        busy: false,
        confirmation: action.prompt,
      };
    case "restore":
      return restored(action.snapshot, action.ids);
    case "reset":
      return initialChatState;
  }
}
