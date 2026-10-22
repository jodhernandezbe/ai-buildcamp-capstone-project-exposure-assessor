import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { LayoutConfig } from "../../types/workspace";
import { SplitWorkspace } from "./SplitWorkspace";

function width(px: number) {
  vi.stubGlobal("matchMedia", (query: string) => {
    const max = Number(/max-width: (\d+)px/.exec(query)?.[1] ?? Infinity);
    return { matches: px <= max, addEventListener: () => undefined, removeEventListener: () => undefined };
  });
}

const LAYOUT: LayoutConfig = {
  rail: { collapsed_px: 60, default_px: 240, min_px: 200, max_px: 320 },
  chat: { default_share: 0.34, min_px: 280, max_share: 0.55 },
  overview: { default_share: 0.4, min_share: 0.15, max_share: 0.75 },
};

const shell = (layout: LayoutConfig | undefined = LAYOUT) =>
  render(
    <SplitWorkspace
      layout={layout}
      narrowBreakpointPx={900}
      rail={({ collapsed, toggle }) => (
        <button type="button" onClick={toggle}>
          rail {collapsed ? "collapsed" : "expanded"}
        </button>
      )}
      overview={<p>overview body</p>}
      map={<p>map body</p>}
      chat={({ collapse }) => (
        <>
          <p>chat body</p>
          <button type="button" onClick={collapse}>
            collapse chat
          </button>
        </>
      )}
    />,
  );

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("SplitWorkspace on a wide viewport", () => {
  it("shows the navigation, both analysis panels and the copilot, with no tabs", () => {
    width(1440);
    shell();
    expect(screen.getByRole("navigation", { name: "Navigation" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Overview" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Map" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Copilot" })).toBeVisible();
    expect(screen.queryByRole("tablist")).toBeNull();
  });

  it("has a keyboard-focusable splitter between each pair of regions", () => {
    width(1440);
    shell();
    for (const name of ["Resize navigation", "Resize overview and map", "Resize copilot"]) {
      const splitter = screen.getByRole("separator", { name });
      expect(splitter).toHaveAttribute("tabindex", "0");
    }
  });

  it("keeps the layout inside the viewport without page scrolling", () => {
    width(1440);
    const { container } = shell();
    expect(container.firstElementChild).toHaveClass("h-dvh", "w-dvw", "overflow-hidden");
  });

  it("works before the layout limits have loaded", () => {
    width(1440);
    shell(undefined);
    expect(screen.getByText("overview body")).toBeInTheDocument();
    expect(screen.getByText("chat body")).toBeInTheDocument();
  });
});

describe("fullscreen", () => {
  it("fills the workspace with one panel, keeps the others mounted but inert, and Escape restores", async () => {
    width(1440);
    const user = userEvent.setup();
    shell();
    const map = screen.getByRole("region", { name: "Map" });
    await user.click(within(map).getByRole("button", { name: "Enter fullscreen" }));
    expect(map).toHaveClass("fixed", "inset-0");
    expect(within(map).getByRole("button", { name: "Exit fullscreen" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Overview", hidden: true })).toHaveAttribute("inert");
    expect(screen.getByRole("region", { name: "Copilot", hidden: true })).toHaveAttribute("inert");
    expect(screen.getByRole("navigation", { name: "Navigation", hidden: true })).toHaveAttribute("inert");
    expect(screen.getByText("chat body")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(map).not.toHaveClass("fixed");
    expect(screen.getByRole("region", { name: "Overview" })).not.toHaveAttribute("inert");
  });

  it("works for the overview panel too, and the toggle exits", async () => {
    width(1440);
    const user = userEvent.setup();
    shell();
    const overview = screen.getByRole("region", { name: "Overview" });
    await user.click(within(overview).getByRole("button", { name: "Enter fullscreen" }));
    expect(overview).toHaveClass("fixed");
    await user.click(within(overview).getByRole("button", { name: "Exit fullscreen" }));
    expect(overview).not.toHaveClass("fixed");
  });

  it("leaves Escape to a layer that already handled it", async () => {
    width(1440);
    const user = userEvent.setup();
    shell();
    const map = screen.getByRole("region", { name: "Map" });
    await user.click(within(map).getByRole("button", { name: "Enter fullscreen" }));
    const handler = (event: KeyboardEvent) => {
      event.preventDefault();
      event.stopPropagation();
    };
    document.addEventListener("keydown", handler);
    await user.keyboard("{Escape}");
    document.removeEventListener("keydown", handler);
    expect(map).toHaveClass("fixed");
  });
});

describe("collapsing the chat", () => {
  it("collapses from the dock, offers a restore control, and keeps the dock mounted", async () => {
    width(1440);
    const user = userEvent.setup();
    shell();
    expect(screen.queryByRole("button", { name: "Show copilot" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "collapse chat" }));
    const overview = screen.getByRole("region", { name: "Overview" });
    expect(await within(overview).findByRole("button", { name: "Show copilot" })).toBeInTheDocument();
    expect(screen.getByText("chat body")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show copilot" }));
    expect(screen.queryByRole("button", { name: "Show copilot" })).toBeNull();
  });
});

describe("SplitWorkspace on a narrow viewport", () => {
  it("stacks the regions behind a segmented control and keeps every region mounted", async () => {
    width(600);
    const user = userEvent.setup();
    shell();
    expect(screen.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("region", { name: "Copilot", hidden: true })).toHaveClass("hidden");
    expect(screen.getByText("chat body")).toBeInTheDocument();
    expect(screen.getByText("map body")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Copilot" }));
    expect(screen.getByRole("region", { name: "Copilot" })).not.toHaveClass("hidden");
  });

  it("shows the navigation as icons only and renders no splitters", () => {
    width(600);
    shell();
    expect(screen.getByRole("button", { name: "rail collapsed" })).toBeInTheDocument();
    expect(screen.queryByRole("separator")).toBeNull();
  });
});
