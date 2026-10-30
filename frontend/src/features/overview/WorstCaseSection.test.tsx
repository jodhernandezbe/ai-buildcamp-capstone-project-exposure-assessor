import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EMPTY_WORKSPACE } from "../../hooks/useWorkspaceStore";
import { facility, scenario } from "../../test/fixtures";
import type { ScenarioDriver, WorkspaceState } from "../../types/workspace";
import { WorstCaseSection } from "./WorstCaseSection";

const driver = (over: Partial<ScenarioDriver>): ScenarioDriver => ({
  pathway_key: "community_inhalation",
  quantity: "hq",
  frs_id: "A",
  facility_name: "Plant A",
  stack_number: 2,
  value: 5,
  ...over,
});

const workspace = (over: Partial<WorkspaceState> = {}): WorkspaceState => ({
  ...EMPTY_WORKSPACE,
  facilities: [
    facility({
      frs_id: "A",
      name: "Plant A",
      scenarios: [
        scenario({ value: 5 }),
        scenario({ quantity: "cancer_risk", quantity_label: "Lifetime cancer risk", value: 1e-6 }),
      ],
    }),
    facility({ frs_id: "B", name: "Plant B", scenarios: [scenario({ value: 2 })] }),
  ],
  scenario_drivers: [driver({}), driver({ quantity: "cancer_risk", value: 1e-6 })],
  ...over,
});

const show = (state: WorkspaceState) => render(<WorstCaseSection workspace={state} digits={3} />);

describe("WorstCaseSection", () => {
  it("says what is missing before any assessment", () => {
    show({ ...EMPTY_WORKSPACE });
    expect(screen.getByText(/No scenario yet/)).toBeInTheDocument();
  });

  it("shows the driving facility's scenario first", () => {
    show(workspace());
    expect(screen.getByText("Plant A")).toBeInTheDocument();
    expect(screen.getByText(/drives this result/)).toBeInTheDocument();
    expect(screen.getByRole("article", { name: /Hazard quotient/ })).toBeInTheDocument();
  });

  it("keeps the other facilities behind a closed control", () => {
    const { container } = show(workspace());
    const details = container.querySelector("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");
    expect(screen.getByText("Other facilities (1)")).toBeInTheDocument();
  });

  it("shows another facility's scenario of the same result, and goes back to the driver", () => {
    show(workspace());
    fireEvent.click(screen.getByRole("button", { name: /Plant B/ }));
    expect(screen.getByText(/another facility/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show the facility that drives it" }));
    expect(screen.getByText(/drives this result/)).toBeInTheDocument();
  });

  it("switches to another result of the same pathway", () => {
    show(workspace());
    fireEvent.click(screen.getByRole("button", { name: "Lifetime cancer risk" }));
    expect(screen.getByRole("article", { name: /Lifetime cancer risk/ })).toBeInTheDocument();
    expect(screen.queryByText(/Other facilities/)).toBeNull(); // only one facility has it
  });

  it("shows a pathway it has never heard of, from the scenario alone", () => {
    const dermal = scenario({
      pathway_key: "dermal_contact",
      pathway: "Soil → Dermal → Child",
      quantity: "dose",
      quantity_label: "Absorbed dose",
      value: 0.4,
      tier: null,
      benchmark: null,
    });
    show(
      workspace({
        facilities: [facility({ frs_id: "A", name: "Plant A", scenarios: [dermal] })],
        scenario_drivers: [driver({ pathway_key: "dermal_contact", quantity: "dose", value: 0.4, stack_number: null })],
      }),
    );
    expect(screen.getByRole("group", { name: "Soil → Dermal → Child" })).toBeInTheDocument();
    expect(screen.getByRole("article", { name: /Absorbed dose/ })).toBeInTheDocument();
  });
});
