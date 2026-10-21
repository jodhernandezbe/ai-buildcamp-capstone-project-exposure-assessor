import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SplitWorkspace } from "./SplitWorkspace";

function width(px: number) {
  vi.stubGlobal("matchMedia", (query: string) => {
    const max = Number(/max-width: (\d+)px/.exec(query)?.[1] ?? Infinity);
    return { matches: px <= max, addEventListener: () => undefined, removeEventListener: () => undefined };
  });
}

const shell = () => render(<SplitWorkspace narrowBreakpointPx={900} left={<p>left</p>} right={<p>right</p>} />);
afterEach(() => vi.unstubAllGlobals());

describe("SplitWorkspace", () => {
  it("shows both panes side by side on a wide viewport", () => {
    width(1440);
    shell();
    expect(screen.getByRole("region", { name: "Overview" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Copilot" })).toBeVisible();
    expect(screen.queryByRole("tablist")).toBeNull();
  });

  it("stacks the panes behind a segmented control on a narrow viewport", async () => {
    width(600);
    const user = userEvent.setup();
    shell();
    expect(screen.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("region", { name: "Copilot", hidden: true })).toHaveClass("hidden");
    await user.click(screen.getByRole("tab", { name: "Copilot" }));
    expect(screen.getByRole("region", { name: "Copilot" })).not.toHaveClass("hidden");
    expect(screen.getByRole("region", { name: "Overview", hidden: true })).toHaveClass("hidden");
  });

  it("keeps both panes mounted so no state is lost", () => {
    width(600);
    shell();
    expect(screen.getByText("right")).toBeInTheDocument();
    expect(screen.getByText("left")).toBeInTheDocument();
  });
});
