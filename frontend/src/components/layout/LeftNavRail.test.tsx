import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { LeftNavRail, type RailRun } from "./LeftNavRail";

const RUNS: RailRun[] = [
  { id: "b", title: "Assess benzene" },
  { id: "a", title: null },
];

function setup(over: Partial<Parameters<typeof LeftNavRail>[0]> = {}) {
  const props = {
    collapsed: false,
    onToggle: vi.fn(),
    runs: RUNS,
    currentId: "b",
    canSwitch: true,
    onNewAnalysis: vi.fn(),
    onSelectRun: vi.fn(),
    onWorkspace: vi.fn(),
    onOpenSettings: vi.fn(),
    ...over,
  };
  render(<LeftNavRail {...props} />);
  return props;
}

describe("LeftNavRail expanded", () => {
  it("shows no toggle where the rail cannot expand", () => {
    setup({ onToggle: undefined });
    expect(screen.queryByRole("button", { name: /navigation/ })).toBeNull();
  });

  it("shows the brand, new analysis, workspace, runs and settings with labels", () => {
    setup();
    expect(screen.getByText("EcoFate")).toBeInTheDocument();
    expect(screen.getByText("Exposure & Risk Studio")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New analysis" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Workspace" })).toHaveAttribute("aria-current", "page");
    const runs = within(screen.getByRole("list", { name: "Runs" }));
    expect(runs.getByRole("button", { name: "Assess benzene" })).toHaveAttribute("aria-current", "true");
    expect(runs.getByRole("button", { name: "Untitled analysis" })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("button", { name: "Settings" })).toBeInTheDocument();
  });

  it("anchors Settings below the runs", () => {
    setup();
    const settings = screen.getByRole("button", { name: "Settings" });
    const list = screen.getByRole("list", { name: "Runs" });
    expect(list.compareDocumentPosition(settings) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("reports each action", async () => {
    const user = userEvent.setup();
    const props = setup();
    await user.click(screen.getByRole("button", { name: "Collapse navigation" }));
    await user.click(screen.getAllByRole("button", { name: /New analysis/ })[0] as HTMLElement);
    await user.click(within(screen.getByRole("list", { name: "Runs" })).getByRole("button", { name: "Untitled analysis" }));
    await user.click(screen.getByRole("button", { name: "Workspace" }));
    await user.click(screen.getByRole("button", { name: "Settings" }));
    expect(props.onToggle).toHaveBeenCalledTimes(1);
    expect(props.onWorkspace).toHaveBeenCalledTimes(1);
    expect(props.onNewAnalysis).toHaveBeenCalledTimes(1);
    expect(props.onSelectRun).toHaveBeenCalledWith("a");
    expect(props.onOpenSettings).toHaveBeenCalledTimes(1);
  });

  it("blocks starting or switching runs while a turn streams, but not the current run or Settings", async () => {
    const user = userEvent.setup();
    const props = setup({ canSwitch: false });
    expect(screen.getAllByRole("button", { name: /New analysis/ })[0]).toBeDisabled();
    const runs = within(screen.getByRole("list", { name: "Runs" }));
    expect(runs.getByRole("button", { name: "Untitled analysis" })).toBeDisabled();
    expect(runs.getByRole("button", { name: "Assess benzene" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "Settings" }));
    expect(props.onOpenSettings).toHaveBeenCalled();
  });
});

describe("LeftNavRail collapsed", () => {
  it("shows icons only, each named and titled", () => {
    setup({ collapsed: true });
    expect(screen.queryByText("EcoFate")).toBeNull();
    expect(screen.getByRole("img", { name: "EcoFate" })).toHaveAttribute("title", "EcoFate");
    for (const name of ["New analysis", "Workspace", "Assess benzene", "Settings", "Expand navigation"]) {
      const button = screen.getAllByRole("button", { name })[0] as HTMLElement;
      expect(button.textContent).toBe("");
    }
    expect(screen.getByRole("button", { name: "Settings" })).toHaveAttribute("title", "Settings");
  });

  it("opens Settings from its icon", async () => {
    const user = userEvent.setup();
    const props = setup({ collapsed: true });
    await user.click(screen.getByRole("button", { name: "Settings" }));
    expect(props.onOpenSettings).toHaveBeenCalled();
  });
});
