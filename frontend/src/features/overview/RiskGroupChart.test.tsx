import { render, screen, within } from "@testing-library/react";
import { cloneElement, type ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import type { Group } from "./riskGroups";
import { BarTooltip, RiskGroupChart, toRows } from "./RiskGroupChart";

// jsdom has no layout, so the responsive wrapper is given a fixed size.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children, { width: 600, height: 300 } as object),
  };
});

const thresholds = { hq_concern: 1, hq_near_lower: 0.1, cancer_lower: 1e-6, cancer_upper: 1e-4 };
const group = (over: Partial<Group> = {}): Group => ({
  key: "325",
  label: "325 · Chemicals",
  facilities: 3,
  assessed: 2,
  screenedOut: 1,
  hq: { value: 5, frsId: "B", name: "Plant B", concentration: 8 },
  risk: { value: 2e-6, frsId: "A", name: "Plant A", concentration: 4 },
  ...over,
});

const props = { thresholds, digits: 2, caption: "Risk by industry", labelChars: 14, heightClass: "h-56", angled: true };

describe("toRows", () => {
  it("keeps only values a logarithmic axis can draw", () => {
    const rows = toRows([group({ hq: { value: 0, frsId: "B", name: null, concentration: null }, risk: null })]);
    expect(rows[0]?.hq).toBeUndefined();
    expect(rows[0]?.risk).toBeUndefined();
    expect(toRows([group()])[0]).toMatchObject({ hq: 5, risk: 2e-6, label: "325 · Chemicals" });
  });
});

describe("BarTooltip", () => {
  const payload = (dataKey: string) => [{ dataKey, payload: toRows([group()])[0] }];

  it("names the group, value, facility, concentration and counts for the hovered bar", () => {
    render(<BarTooltip active payload={payload("hq")} digits={2} />);
    expect(screen.getByText("325 · Chemicals")).toBeInTheDocument();
    expect(screen.getByText("Highest hazard quotient: 5")).toBeInTheDocument();
    expect(screen.getByText("Facility: Plant B (FRS B)")).toBeInTheDocument();
    expect(screen.getByText("Worst-case concentration: 8 µg/m³")).toBeInTheDocument();
    expect(screen.getByText("3 facilities, 2 assessed, 1 screened out")).toBeInTheDocument();
  });

  it("describes the cancer-risk bar with its own facility", () => {
    render(<BarTooltip active payload={payload("risk")} digits={2} />);
    expect(screen.getByText("Facility: Plant A (FRS A)")).toBeInTheDocument();
    expect(screen.getByText("Worst-case concentration: 4 µg/m³")).toBeInTheDocument();
  });

  it("shows nothing when inactive or without a bar", () => {
    const { container, rerender } = render(<BarTooltip active={false} payload={payload("hq")} digits={2} />);
    expect(container).toBeEmptyDOMElement();
    rerender(<BarTooltip active payload={[]} digits={2} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("RiskGroupChart", () => {
  it("draws the three thresholds and lists the series and the thresholds in words", () => {
    const { container } = render(<RiskGroupChart groups={[group()]} {...props} />);
    expect(container.querySelectorAll(".recharts-reference-line")).toHaveLength(3);
    expect(screen.getByText("Hazard quotient (non-cancer)")).toBeInTheDocument();
    expect(screen.getByText("Lifetime cancer risk")).toBeInTheDocument();
    expect(screen.getByText(/thresholds of concern \(HQ 1, cancer risk 1 × 10⁻⁶ to 1 × 10⁻⁴\)/)).toBeInTheDocument();
  });

  it("draws no threshold lines without thresholds", () => {
    const { container } = render(<RiskGroupChart groups={[group()]} {...props} thresholds={undefined} />);
    expect(container.querySelectorAll(".recharts-reference-line")).toHaveLength(0);
  });

  it("has every bar as text, including values the log axis cannot draw", () => {
    const zero = group({ key: "9", label: "9 · Zero", hq: { value: 0, frsId: "Z", name: "Plant Z", concentration: 0 }, risk: null });
    render(<RiskGroupChart groups={[group(), zero]} {...props} />);
    const table = screen.getByRole("table", { name: "Risk by industry" });
    const rows = within(table).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(rows[1]).toHaveTextContent("325 · Chemicals");
    expect(rows[1]).toHaveTextContent("5 (Plant B)");
    expect(rows[1]).toHaveTextContent("2 × 10⁻⁶ (Plant A)");
    expect(rows[2]).toHaveTextContent("0 (Plant Z)");
    expect(rows[2]).toHaveTextContent("not reported");
  });
});
