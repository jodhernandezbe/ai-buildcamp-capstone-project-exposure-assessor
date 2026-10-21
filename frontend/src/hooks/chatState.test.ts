import type { StreamEvent } from "../types/workspace";
import { chatReducer, initialChatState, type ChatState } from "./chatState";

const token = (text: string): StreamEvent => ({ type: "token", seq: 1, text });
const sent: ChatState = chatReducer(initialChatState, {
  type: "user_sent",
  id: "u1",
  assistantId: "a1",
  text: "hello",
});

describe("chatReducer", () => {
  it("adds the user message and a streaming assistant placeholder", () => {
    expect(sent.busy).toBe(true);
    expect(sent.messages.map((m) => [m.role, m.text, m.streaming])).toEqual([
      ["user", "hello", false],
      ["assistant", "", true],
    ]);
  });

  it("appends tokens to the assistant message", () => {
    let state = chatReducer(sent, { type: "event", event: token("Hel") });
    state = chatReducer(state, { type: "event", event: token("lo") });
    expect(state.messages[1]?.text).toBe("Hello");
  });

  it("keeps streamed text when the final message arrives", () => {
    let state = chatReducer(sent, { type: "event", event: token("Hello there") });
    const final: StreamEvent = { type: "assistant_message", seq: 2, text: "Hello there" };
    state = chatReducer(state, { type: "event", event: final });
    expect(state.messages[1]?.text).toBe("Hello there");
  });

  it("uses the final message when the model did not stream", () => {
    const final: StreamEvent = { type: "assistant_message", seq: 2, text: "Hello there" };
    const state = chatReducer(sent, { type: "event", event: final });
    expect(state.messages[1]?.text).toBe("Hello there");
  });

  describe("tool steps", () => {
    const status = (
      phase: "started" | "finished",
      id: string,
      label: string,
      outcome: "ok" | "error" | null = null,
    ): StreamEvent => ({
      type: "tool_status",
      seq: 1,
      phase,
      call_id: id,
      tool_name: "t",
      label,
      status: outcome,
    });
    const apply = (state: ChatState, event: StreamEvent) =>
      chatReducer(state, { type: "event", event });

    it("adds a running step and then marks it done", () => {
      let state = apply(sent, status("started", "c1", "Queried EPA TRI releases"));
      expect(state.messages[1]?.tools).toEqual([
        { callId: "c1", label: "Queried EPA TRI releases", state: "running" },
      ]);
      state = apply(state, status("finished", "c1", "Queried EPA TRI releases", "ok"));
      expect(state.messages[1]?.tools[0]?.state).toBe("done");
    });

    it("marks a failed step as error and keeps the others", () => {
      let state = apply(sent, status("started", "c1", "One"));
      state = apply(state, status("started", "c2", "Two"));
      state = apply(state, status("finished", "c2", "Two", "error"));
      expect(state.messages[1]?.tools.map((s) => [s.callId, s.state])).toEqual([
        ["c1", "running"],
        ["c2", "error"],
      ]);
    });

    it("ignores a repeated start and tolerates a finish with no start", () => {
      let state = apply(sent, status("started", "c1", "One"));
      state = apply(state, status("started", "c1", "One"));
      state = apply(state, status("finished", "c9", "Nine", "ok"));
      expect(state.messages[1]?.tools.map((s) => s.callId)).toEqual(["c1", "c9"]);
    });

    it("separates narration before a tool from the text after it", () => {
      let state = apply(sent, token("Let me check."));
      state = apply(state, status("started", "c1", "One"));
      state = apply(state, token("Done."));
      expect(state.messages[1]?.text).toBe("Let me check.\n\nDone.");
    });
  });

  it("shows an error event on the assistant message and ends the turn", () => {
    const error: StreamEvent = { type: "error", seq: 1, message: "Add your key", correlation_id: "c" };
    let state = chatReducer(sent, { type: "event", event: error });
    state = chatReducer(state, { type: "event", event: { type: "turn_finished", seq: 2 } });
    expect(state.messages[1]).toMatchObject({ error: "Add your key", streaming: false });
    expect(state.busy).toBe(false);
  });

  it("marks the turn failed when the request itself fails", () => {
    const state = chatReducer(sent, { type: "failed", message: "Request failed (500)." });
    expect(state.busy).toBe(false);
    expect(state.messages[1]).toMatchObject({ error: "Request failed (500).", streaming: false });
  });

  it("closes a stream that ended without turn_finished", () => {
    const state = chatReducer(sent, { type: "closed" });
    expect(state.busy).toBe(false);
    expect(state.messages[1]?.streaming).toBe(false);
  });

  it("shows the redirect for an off-topic turn as the assistant's message, not an error", () => {
    const scope: StreamEvent = { type: "scope", seq: 1, in_scope: false };
    const pivot: StreamEvent = { type: "guardrail_pivot", seq: 2, text: "I can't help with that." };
    let state = chatReducer(sent, { type: "event", event: scope });
    state = chatReducer(state, { type: "event", event: pivot });
    state = chatReducer(state, { type: "event", event: { type: "turn_finished", seq: 3 } });
    expect(state.messages[1]).toMatchObject({
      text: "I can't help with that.",
      error: null,
      streaming: false,
      tools: [],
    });
    expect(state.busy).toBe(false);
  });

  it("keeps the latest usage and clears it on reset", () => {
    const totals = {
      calls: 1,
      input_tokens: 5,
      cached_input_tokens: 0,
      output_tokens: 6,
      complete: true,
      cost_usd: null,
      cost_status: "unpriced" as const,
      priced_on: null,
    };
    const usage: StreamEvent = { type: "usage", seq: 3, turn: totals, session: totals };
    const state = chatReducer(sent, { type: "event", event: usage });
    expect(state.usage).toEqual(usage);
    expect(state.busy).toBe(true); // usage does not end the turn; turn_finished does
    expect(chatReducer(state, { type: "reset" }).usage).toBeNull();
  });

  it("ignores events with no chat meaning and resets", () => {
    const scope: StreamEvent = { type: "scope", seq: 1, in_scope: true };
    expect(chatReducer(sent, { type: "event", event: scope })).toBe(sent);
    expect(chatReducer(sent, { type: "reset" })).toEqual(initialChatState);
  });
});
