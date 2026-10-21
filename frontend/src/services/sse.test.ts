import { parseSseFrames } from "./sse";

const frame = (event: object) => `data: ${JSON.stringify(event)}\n\n`;

describe("parseSseFrames", () => {
  it("returns every complete event in order", () => {
    const text = frame({ type: "turn_started", seq: 0 }) + frame({ type: "token", seq: 1, text: "hi" });
    const { events, rest } = parseSseFrames(text);
    expect(events.map((e) => e.type)).toEqual(["turn_started", "token"]);
    expect(rest).toBe("");
  });

  it("keeps an unfinished frame for the next chunk", () => {
    const whole = frame({ type: "token", seq: 1, text: "hello" });
    const first = parseSseFrames(whole.slice(0, 15));
    expect(first.events).toEqual([]);
    const second = parseSseFrames(first.rest + whole.slice(15));
    expect(second.events).toHaveLength(1);
    expect(second.rest).toBe("");
  });

  it("ignores comment and empty frames", () => {
    const { events } = parseSseFrames(": ping\n\n" + frame({ type: "token", seq: 0, text: "a" }));
    expect(events).toHaveLength(1);
  });

  it("rejects a malformed event instead of guessing", () => {
    expect(() => parseSseFrames("data: {not json\n\n")).toThrow("Malformed event");
    expect(() => parseSseFrames('data: {"no_type": 1}\n\n')).toThrow("Malformed event");
  });
});
