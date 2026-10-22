import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "./App";
import { EMPTY_WORKSPACE } from "./hooks/useWorkspaceStore";
import { FakeMap } from "./test/fakeMaplibre";
import { extremum, workspace } from "./test/fixtures";

const TOTALS = {
  calls: 1,
  input_tokens: 10,
  cached_input_tokens: 0,
  output_tokens: 5,
  complete: true,
  cost_usd: null,
  cost_status: "unpriced",
  priced_on: null,
};

const REVIEWED = workspace({
  framing_version: 3,
  risk: { ...EMPTY_WORKSPACE.risk, hq_worst: extremum(2.5, "above"), reason: null },
});

interface Stub {
  calls: string[];
  snapshot: (id: string) => Response;
}

const CONFIG = {
  model: "m",
  suggestions: ["Assess benzene"],
  map: {
    light_style: "l",
    dark_style: "d",
    marker_min_px: 4,
    marker_max_px: 9,
    initial_view: { west: -125, south: 24.5, east: -66.9, north: 49.5 },
  },
};

function stub(options: { never?: boolean } = {}): Stub {
  const state: Stub = {
    calls: [],
    snapshot: () =>
      new Response(
        JSON.stringify({
          thread_id: "x",
          messages: [
            { role: "user", text: "Assess benzene" },
            { role: "assistant", text: "Restored answer" },
          ],
          workspace: REVIEWED,
          usage: TOTALS,
        }),
        { status: 200 },
      ),
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      state.calls.push(`${init?.method ?? "GET"} ${url}`);
      if (url.endsWith("/settings/client")) return Promise.resolve(new Response(JSON.stringify(CONFIG)));
      if (url.endsWith("/settings/keys")) {
        const body = { openai: { configured: true }, census: { configured: false }, comptox: { configured: false } };
        return Promise.resolve(new Response(JSON.stringify(body)));
      }
      if (url.includes("/chat/threads/")) return Promise.resolve(state.snapshot(url));
      const open = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ type: "token", seq: 0, text: "Hi" })}\n\n`));
          if (!options.never) {
            controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ type: "turn_finished", seq: 1 })}\n\n`));
            controller.close();
          }
        },
      });
      return Promise.resolve(new Response(open, { status: 200 }));
    }),
  );
  return state;
}

const rail = () => within(screen.getByRole("navigation", { name: "Navigation" }));
const chat = () => within(screen.getByRole("region", { name: "Copilot" }));

async function runOnce(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await chat().findByRole("button", { name: "Assess benzene" }));
  await screen.findByText("Hi");
  await waitFor(() => expect(chat().getByLabelText("Message")).toBeEnabled());
}

beforeEach(() => FakeMap.reset());
afterEach(() => vi.unstubAllGlobals());

describe("session run history", () => {
  it("lists the first run as New analysis, titles it by its first message, and adds a run on New analysis", async () => {
    stub();
    const user = userEvent.setup();
    render(<App />);
    const runs = () => within(rail().getByRole("list", { name: "Runs" }));
    expect(runs().getByRole("button", { name: "Untitled analysis" })).toBeInTheDocument();
    // An empty run is not started twice.
    await user.click(rail().getByRole("button", { name: "New analysis" }));
    expect(runs().getAllByRole("button")).toHaveLength(1);
    await runOnce(user);
    expect(runs().getByRole("button", { name: "Assess benzene" })).toHaveAttribute("aria-current", "true");
    await user.click(rail().getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    expect(runs().getAllByRole("button")).toHaveLength(2);
    expect(runs().getByRole("button", { name: "Untitled analysis" })).toHaveAttribute("aria-current", "true");
  });

  it("restores an earlier run's messages and workspace and continues it", async () => {
    const api = stub();
    const user = userEvent.setup();
    render(<App />);
    await runOnce(user);
    await user.click(rail().getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    expect(screen.queryByText("Hi")).toBeNull();
    await user.click(within(rail().getByRole("list", { name: "Runs" })).getByRole("button", { name: "Assess benzene" }));
    expect(await screen.findByText("Restored answer")).toBeInTheDocument();
    expect((await screen.findAllByText("Above concern")).length).toBeGreaterThan(0);
    expect(api.calls.some((call) => call.startsWith("GET") && call.includes("/chat/threads/"))).toBe(true);
    expect(chat().getByLabelText("Message")).toBeEnabled();
  });

  it("says a run is gone, drops it from the list and keeps the current conversation", async () => {
    const api = stub();
    const user = userEvent.setup();
    render(<App />);
    await runOnce(user);
    await user.click(rail().getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    api.snapshot = () => new Response(JSON.stringify({ error: "gone", correlation_id: "c" }), { status: 404 });
    await user.click(within(rail().getByRole("list", { name: "Runs" })).getByRole("button", { name: "Assess benzene" }));
    expect(await chat().findByText("That run is no longer available.")).toBeInTheDocument();
    expect(within(rail().getByRole("list", { name: "Runs" })).queryByRole("button", { name: "Assess benzene" })).toBeNull();
    expect(chat().getByRole("button", { name: "Assess benzene" })).toBeInTheDocument(); // still the empty new run
  });

  it("cannot be left while a turn is streaming", async () => {
    stub({ never: true });
    const user = userEvent.setup();
    render(<App />);
    await user.click(await chat().findByRole("button", { name: "Assess benzene" }));
    await screen.findByText("Hi");
    expect(rail().getAllByRole("button", { name: /New analysis/ })[0]).toBeDisabled();
  });

  it("keeps the run list out of browser storage", async () => {
    stub();
    localStorage.clear();
    sessionStorage.clear();
    const user = userEvent.setup();
    render(<App />);
    await runOnce(user);
    await user.click(rail().getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("Assess benzene");
  });
});

describe("the map across runs", () => {
  it("reframes onto the United States when a new analysis empties the workspace", async () => {
    stub();
    const user = userEvent.setup();
    render(<App />);
    await runOnce(user);
    await waitFor(() => expect(FakeMap.instances.length).toBeGreaterThan(0));
    const map = FakeMap.last;
    const before = map.fits.length;
    await user.click(rail().getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    await waitFor(() => expect(map.fits.length).toBe(before + 1));
    expect(map.fits.at(-1)?.bounds).toEqual([
      [-125, 24.5],
      [-66.9, 49.5],
    ]);
  });
});
