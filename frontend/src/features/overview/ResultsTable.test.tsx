import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { facility } from "../../test/fixtures";
import { ResultsTable } from "./ResultsTable";

const extreme = (high: number) => ({ low: high / 2, high, low_stack: 1, high_stack: 2 });
const exposure = (hq: number) => ({
  stacks_given: 2,
  stacks_evaluated: 2,
  hq_worst: extreme(hq),
  hq_representative: extreme(hq / 10),
  cancer_risk_worst: null,
  cancer_risk_representative: null,
  concentration_worst: null,
  concentration_representative: null,
  warnings: [],
});
const receptors = { total_population: 1234, radius_km: 1.6, age_distribution: {}, source: "s", screening_default: false, warnings: [] };
const above = facility({ frs_id: "A", name: "Alpha Plant", state: "TX", status: "above", exposure: exposure(5), receptors });
const near = facility({ frs_id: "N", name: "Near Works", status: "near", exposure: exposure(0.5) });
const out = facility({
  frs_id: "O",
  name: "Outer",
  status: "below",
  screening: { outcome: "screened_out_at_bound", bound_hq: 0.05, bound_cancer_risk: null, value_hq: 0.05, value_cancer_risk: null, reason: "r" },
});

const names = () =>
  within(screen.getByRole("table")).getAllByRole("button", { name: /Show .* on the map/ }).map((b) => b.textContent);

describe("ResultsTable", () => {
  it("renders nothing without facilities", () => {
    const { container } = render(<ResultsTable facilities={[]} digits={2} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("lists the assessed facilities by status then HQ, with their values as sent", () => {
    render(<ResultsTable facilities={[near, above, out]} digits={2} />);
    expect(names()).toEqual(["Alpha Plant", "Near Works"]);
    const row = screen.getByRole("row", { name: /Alpha Plant/ });
    expect(row).toHaveTextContent("2.5 – 5");
    expect(row).toHaveTextContent("1,234");
    expect(row).toHaveTextContent("Fully assessed");
    expect(screen.getByText("2 assessed · 1 screened out or not assessed")).toBeInTheDocument();
  });

  it("folds the screened-out facilities and shows their screening value in place of the HQ", async () => {
    const user = userEvent.setup();
    render(<ResultsTable facilities={[above, out]} digits={2} />);
    expect(screen.queryByText("Outer")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Show 1 screened out or not assessed" }));
    const row = screen.getByRole("row", { name: /Outer/ });
    expect(row).toHaveTextContent("screened out (bound: HQ 0.05)");
    expect(row).toHaveTextContent("Screened out on the bound");
  });

  it("sorts by a column when its header is activated, and reverses on a second activation", async () => {
    const user = userEvent.setup();
    render(<ResultsTable facilities={[near, above]} digits={2} />);
    const header = screen.getByRole("button", { name: "Facility" });
    await user.click(header);
    expect(names()).toEqual(["Alpha Plant", "Near Works"]);
    expect(screen.getByRole("columnheader", { name: "Facility" })).toHaveAttribute("aria-sort", "ascending");
    await user.click(header);
    expect(names()).toEqual(["Near Works", "Alpha Plant"]);
  });

  it("asks to show a facility on the map when its name is activated", async () => {
    const user = userEvent.setup();
    const onFocus = vi.fn();
    render(<ResultsTable facilities={[above]} digits={2} onFocus={onFocus} />);
    await user.click(screen.getByRole("button", { name: "Show Alpha Plant on the map" }));
    expect(onFocus).toHaveBeenCalledWith("A");
  });
});
