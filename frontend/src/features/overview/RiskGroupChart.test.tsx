import { render, screen, within } from "@testing-library/react";
import { cloneElement, type ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import type { Group } from "./riskGroups";
import { BarTooltip, RiskGroupChart, thresholdLines, toRows, workerLines } from "./RiskGroupChart";

// jsdom has no layout, so the responsive wrapper is given a fixed size.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children, { width: 600, height: 300 } as object),
  };
});

const thresholds = { hq_concern: 1, hq_near_lower: 0.5, cancer_lower: 1e-6, cancer_upper: 1e-4 };
const group = (over: Partial<Group> = {}): Group => ({
  key: "325",
  label: "325 · Chemicals",
  facilities: 3,
  assessed: 2,
  screenedOut: 1,
  hq: { value: 5, frsId: "B", name: "Plant B", concentration: 8, twa: null, stack: 2 },
  risk: { value: 2e-6, frsId: "A", name: "Plant A", concentration: 4, twa: null, stack: 1 },
  ratio: null,
  ...over,
});

const props = { thresholds, digits: 2, labelChars: 14, heightClass: "h-56", angled: true };

describe("toRows", () => {
  it("takes the quantity's own value and keeps only one a logarithmic axis can draw", () => {
    expect(toRows([group()], "hq")[0]).toMatchObject({ value: 5, label: "325 · Chemicals" });
    expect(toRows([group()], "risk")[0]?.value).toBe(2e-6);
    const zero = group({ hq: { value: 0, frsId: "B", name: null, concentration: null, twa: null, stack: null } });
    expect(toRows([zero], "hq")[0]?.value).toBeUndefined();
  });
});

describe("thresholdLines", () => {
  it("are the near and concern lines for the hazard quotient", () => {
    expect(thresholdLines("hq", thresholds)).toEqual([
      { y: 0.5, text: "near 0.5" },
      { y: 1, text: "concern 1" },
    ]);
  });

  it("are the lower and upper lines for the cancer risk", () => {
    expect(thresholdLines("risk", thresholds)).toEqual([
      { y: 1e-6, text: "lower 1e-6" },
      { y: 1e-4, text: "upper 1e-4" },
    ]);
  });
});

describe("BarTooltip", () => {
  const payload = (quantity: "hq" | "risk") => [{ payload: toRows([group()], quantity)[0] }];

  it("tells the hazard quotient bar's value, facility, concentration and counts", () => {
    render(<BarTooltip active payload={payload("hq")} quantity="hq" digits={2} />);
    expect(screen.getByText("325 · Chemicals")).toBeInTheDocument();
    expect(screen.getByText("Highest hazard quotient:")).toBeInTheDocument();
    expect(screen.getByText("Plant B · stack 2 · 8 µg/m³ worst case")).toBeInTheDocument();
    expect(screen.getByText("3 facilities in this group · 2 assessed, 1 screened out")).toBeInTheDocument();
    expect(screen.queryByText(/cancer/)).toBeNull();
  });

  it("tells the cancer risk bar's own facility", () => {
    render(<BarTooltip active payload={payload("risk")} quantity="risk" digits={2} />);
    expect(screen.getByText("Highest lifetime cancer risk:")).toBeInTheDocument();
    expect(screen.getByText("Plant A · stack 1 · 4 µg/m³ worst case")).toBeInTheDocument();
    expect(screen.queryByText(/hazard quotient/)).toBeNull();
  });

  it("shows nothing when inactive or without a bar", () => {
    const { container, rerender } = render(<BarTooltip active={false} payload={payload("hq")} quantity="hq" digits={2} />);
    expect(container).toBeEmptyDOMElement();
    rerender(<BarTooltip active payload={[]} quantity="hq" digits={2} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("RiskGroupChart", () => {
  it("is titled, with one axis and the quantity's two threshold lines named", () => {
    const { container } = render(<RiskGroupChart groups={[group()]} quantity="hq" title="Hazard quotient" {...props} />);
    expect(screen.getByRole("heading", { name: "Hazard quotient" })).toBeInTheDocument();
    expect(container.querySelectorAll(".recharts-reference-line")).toHaveLength(2);
    expect(container.querySelectorAll(".recharts-yAxis")).toHaveLength(1);
    expect(screen.getByText("Dashed lines: near 0.5, concern 1")).toBeInTheDocument();
  });

  it("draws the cancer risk chart with its own thresholds", () => {
    render(<RiskGroupChart groups={[group()]} quantity="risk" title="Cancer" {...props} />);
    expect(screen.getByText("Dashed lines: lower 1e-6, upper 1e-4")).toBeInTheDocument();
  });

  it("draws no threshold lines without thresholds", () => {
    const { container } = render(<RiskGroupChart groups={[group()]} quantity="hq" title="HQ" {...props} thresholds={undefined} />);
    expect(container.querySelectorAll(".recharts-reference-line")).toHaveLength(0);
  });

  it("has every bar as text, including a value the log axis cannot draw", () => {
    const zero = group({ key: "9", label: "9 · Zero", hq: { value: 0, frsId: "Z", name: "Plant Z", concentration: 0, twa: null, stack: null }, risk: null });
    render(<RiskGroupChart groups={[group(), zero]} quantity="hq" title="Hazard quotient" {...props} />);
    const rows = within(screen.getByRole("table", { name: "Hazard quotient" })).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(rows[1]).toHaveTextContent("325 · Chemicals");
    expect(rows[1]).toHaveTextContent("5 (Plant B)");
    expect(rows[2]).toHaveTextContent("0 (Plant Z)");
  });
});

const workerLimits = {
  ratio_exceedance: 1,
  ratio_elevated: 0.1,
  hq_exceedance: 1,
  hq_elevated: 0.1,
  cancer_exceedance: 1e-4,
  cancer_elevated: 1e-6,
};

describe("workerLines", () => {
  it("draws the tier boundaries of each worker quantity from the settings", () => {
    expect(workerLines("ratio", workerLimits)).toEqual([
      { y: 0.1, text: "elevated 0.1" },
      { y: 1, text: "exceedance 1" },
    ]);
    expect(workerLines("risk", workerLimits).map((l) => l.y)).toEqual([1e-6, 1e-4]);
    expect(workerLines("hq", { ...workerLimits, hq_elevated: 0.3 })[0]?.y).toBe(0.3);
  });
});

describe("RiskGroupChart on the indoor air pathway", () => {
  it("names the worker boundaries, not the community thresholds", () => {
    render(
      <RiskGroupChart
        {...props}
        groups={[group()]}
        quantity="ratio"
        pathway="indoor"
        workerThresholds={workerLimits}
        title="Ratio"
      />,
    );
    expect(screen.getByText(/Dashed lines: elevated 0\.1, exceedance 1/)).toBeInTheDocument();
    expect(screen.queryByText(/concern/)).toBeNull();
  });

  it("draws no lines when the worker boundaries are not known", () => {
    render(<RiskGroupChart {...props} groups={[group()]} quantity="hq" pathway="indoor" title="HQ" />);
    expect(screen.queryByText(/Dashed lines/)).toBeNull();
  });
});
