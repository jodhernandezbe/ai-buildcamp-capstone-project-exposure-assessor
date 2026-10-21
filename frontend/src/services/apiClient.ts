import type {
  ChatRequest,
  ClientConfig,
  KeyName,
  KeysStatusResponse,
  KeyStatusResponse,
  StreamEvent,
} from "../types/workspace";
import { parseSseFrames } from "./sse";

const BASE = "/api/v1";
const JSON_HEADERS = { "content-type": "application/json" };

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "error" in body) {
      const { error } = body as { error: unknown };
      if (typeof error === "string") return error;
    }
  } catch {
    // not a JSON error body
  }
  return `Request failed (${response.status}).`;
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(BASE + path, init);
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status);
  return response;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  // First-party API whose shapes are generated from its schemas (see src/types).
  return (await (await request(path, init)).json()) as T;
}

export const getClientConfig = (): Promise<ClientConfig> => json("/settings/client");

const KEY_PATHS: Record<KeyName, string> = {
  openai: "openai-key",
  census: "census-key",
  comptox: "comptox-key",
};

export const getKeysStatus = (): Promise<KeysStatusResponse> => json("/settings/keys");

export const saveKey = (name: KeyName, apiKey: string): Promise<KeyStatusResponse> =>
  json(`/settings/${KEY_PATHS[name]}`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ api_key: apiKey }),
  });

export const clearKey = (name: KeyName): Promise<KeyStatusResponse> =>
  json(`/settings/${KEY_PATHS[name]}`, { method: "DELETE" });

export async function resetThread(threadId: string): Promise<void> {
  await request(`/chat/threads/${encodeURIComponent(threadId)}`, { method: "DELETE" });
}

/** Stream the events of one chat turn as they arrive. */
export async function* streamChat(
  body: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const response = await request("/chat/stream", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
    signal,
  });
  if (!response.body) throw new ApiError("The server sent no stream.", response.status);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseFrames(buffer);
    buffer = rest;
    yield* events;
  }
}
