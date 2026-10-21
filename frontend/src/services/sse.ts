import type { StreamEvent } from "../types/workspace";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseEvent(data: string): StreamEvent {
  let value: unknown;
  try {
    value = JSON.parse(data);
  } catch {
    throw new Error("Malformed event from the server.");
  }
  if (!isRecord(value) || typeof value.type !== "string") {
    throw new Error("Malformed event from the server.");
  }
  // The server's events follow the generated contract (checked by the contract tests).
  return value as unknown as StreamEvent;
}

/** Split buffered SSE text into complete events and the unfinished remainder. */
export function parseSseFrames(buffer: string): { events: StreamEvent[]; rest: string } {
  const frames = buffer.split("\n\n");
  const rest = frames.pop() ?? "";
  const events: StreamEvent[] = [];
  for (const frame of frames) {
    const data = frame
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice("data: ".length))
      .join("\n");
    if (data) events.push(parseEvent(data));
  }
  return { events, rest };
}
