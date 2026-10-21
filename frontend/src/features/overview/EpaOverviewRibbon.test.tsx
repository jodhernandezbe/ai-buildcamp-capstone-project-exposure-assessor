import { render, screen, within } from "@testing-library/react";

import { EMPTY_WORKSPACE } from "../../hooks/useWorkspaceStore";
import { extremum, workspace } from "../../test/fixtures";
import { EpaOverviewRibbon } from "./EpaOverviewRibbon";

const card = (name: string) => screen.getByRole("region", { name });

describe("risk card", () => {
  it("says nothing is computed yet, with the reason", () => {
    render(<EpaOverviewRibbon workspace={EMPTY_WORKSPACE} digits={2} />);
    const risk = within(card("Hazard quotient & cancer risk"));
    expect(risk.getAllByText("Not computed")).toHaveLength(2);
    expect(risk.getByText(/not yet computed/)).toBeInTheDocument();
  });

  it("shows the worst case with its status and where it came from", () => {
    const state = workspace({
      risk: { ...EMPTY_WORKSPACE.risk, hq_worst: extremum(2.5, "above", 3), hq_representative: extremum(1.24, "above"), reason: null },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    const risk = within(card("Hazard quotient & cancer risk"));
    expect(risk.getByText("2.5")).toBeInTheDocument();
    expect(risk.getByText("1.2")).toBeInTheDocument();
    expect(risk.getByText("Above concern")).toBeInTheDocument();
    expect(risk.getByText("Plant F1 · stack 3")).toBeInTheDocument();
  });

  it("writes cancer risk in scientific notation", () => {
    const state = workspace({
      risk: { ...EMPTY_WORKSPACE.risk, cancer_risk_worst: extremum(0.000012, "near"), reason: null },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    expect(screen.getByText("1.2 × 10⁻⁵")).toBeInTheDocument();
    expect(screen.getByText("Near concern")).toBeInTheDocument();
  });
});

describe("provenance card", () => {
  it("is not evaluated until the read-across tool ran", () => {
    render(<EpaOverviewRibbon workspace={EMPTY_WORKSPACE} digits={2} />);
    expect(within(card("Chemical & provenance")).getByText("Not evaluated")).toBeInTheDocument();
    expect(screen.queryByText("Direct TRI match")).toBeNull();
  });

  it("shows the properties with their sources, and absent ones as not reported", () => {
    const state = workspace({
      chemical: {
        ...EMPTY_WORKSPACE.chemical,
        cas_number: "1-1-1",
        molecular_weight_g_mol: 50,
        rfc_mg_m3: 0.5,
        sources: { rfc: "IRIS" },
      },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    const chem = within(card("Chemical & provenance"));
    expect(chem.getByText("50 g/mol")).toBeInTheDocument();
    expect(chem.getByText("0.5 mg/m³")).toBeInTheDocument();
    expect(chem.getByText(/Inhalation RfC · IRIS/)).toBeInTheDocument();
    expect(chem.getByText("not reported")).toBeInTheDocument(); // the unit risk
  });

  it("shows a surrogate with its scores inside the applicability domain", () => {
    const state = workspace({
      chemical: {
        ...EMPTY_WORKSPACE.chemical,
        read_across: {
          ...EMPTY_WORKSPACE.chemical.read_across,
          kind: "read_across",
          surrogate_cas: "9-9-9",
          surrogate_name: "Synthetic surrogate",
          hybrid_score: 0.4,
          cosine_similarity: 0.5,
          tanimoto_similarity: 0.25,
          within_applicability_domain: true,
        },
      },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    const chem = within(card("Chemical & provenance"));
    expect(chem.getByText("Read-across surrogate")).toBeInTheDocument();
    expect(chem.getByText("Synthetic surrogate")).toBeInTheDocument();
    expect(chem.getByText("0.4")).toBeInTheDocument();
    expect(chem.getByText("Within applicability domain")).toBeInTheDocument();
  });

  it("flags a surrogate outside the applicability domain", () => {
    const state = workspace({
      chemical: {
        ...EMPTY_WORKSPACE.chemical,
        read_across: { ...EMPTY_WORKSPACE.chemical.read_across, kind: "read_across", within_applicability_domain: false },
      },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    expect(screen.getByText("Outside applicability domain")).toBeInTheDocument();
  });

  it.each([
    ["direct_tri_match", "Direct TRI match"],
    ["unresolved", "Unresolved"],
  ] as const)("badges %s", (kind, label) => {
    const state = workspace({
      chemical: { ...EMPTY_WORKSPACE.chemical, read_across: { ...EMPTY_WORKSPACE.chemical.read_across, kind } },
    });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

describe("population card", () => {
  const receptors = {
    total_population: 12345,
    radius_km: 3,
    age_distribution: { "0-4": 10, "5-17": 20, "18-64": 50, "65+": 20 },
    source: "synthetic ACS",
    screening_default: false,
    warnings: [],
  };

  it("is empty until receptors are reported", () => {
    render(<EpaOverviewRibbon workspace={EMPTY_WORKSPACE} digits={2} />);
    expect(screen.getByText("Population not reported yet.")).toBeInTheDocument();
  });

  it("shows residents, radius and the four age bands", () => {
    render(<EpaOverviewRibbon workspace={workspace({ receptors })} digits={2} />);
    const pop = within(card("Exposed population"));
    expect(pop.getByText("12,345")).toBeInTheDocument();
    expect(pop.getByText("3 km")).toBeInTheDocument();
    expect(pop.getByRole("img", { name: "0-4: 10%, 5-17: 20%, 18-64: 50%, 65+: 20%" })).toBeInTheDocument();
    expect(pop.queryByText("screening default")).toBeNull();
  });

  it("marks a screening default", () => {
    render(<EpaOverviewRibbon workspace={workspace({ receptors: { ...receptors, screening_default: true } })} digits={2} />);
    expect(screen.getByText("screening default")).toBeInTheDocument();
  });
});

describe("meteorology card", () => {
  const weather = {
    wind_speed_m_s: 3,
    wind_from_deg: 270,
    wind_toward_deg: 90,
    ambient_temperature_k: 290,
    stability_class: "D",
    source: "synthetic 2020",
    screening_default: false,
    latitude: 29.72,
    longitude: -95.25,
    frs_id: "F1",
    facility_name: "Plant F1",
    warnings: [],
  };

  it("says which facility the weather is for", () => {
    render(<EpaOverviewRibbon workspace={workspace({ meteorology: weather })} digits={2} />);
    expect(within(card("Meteorology")).getByText("For Plant F1")).toBeInTheDocument();
  });

  it("says when the weather is for a point that is not one of the facilities", () => {
    const state = workspace({ meteorology: { ...weather, frs_id: null, facility_name: null } });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    expect(within(card("Meteorology")).getByText("At 29.720, -95.250 (not one of the facilities)")).toBeInTheDocument();
  });

  it("shows the wind, temperature and class with the arrow pointing downwind", () => {
    const { container } = render(<EpaOverviewRibbon workspace={workspace({ meteorology: weather })} digits={2} />);
    const met = within(card("Meteorology"));
    expect(met.getByText("3 m/s")).toBeInTheDocument();
    expect(met.getByText("270°")).toBeInTheDocument();
    expect(met.getByText("290 K")).toBeInTheDocument();
    expect(met.getByText("D")).toBeInTheDocument();
    expect(container.querySelector<SVGElement>("svg")?.style.transform).toBe("rotate(90deg)");
  });

  it("marks default weather as a screening default", () => {
    const state = workspace({ meteorology: { ...weather, source: "screening default", screening_default: true } });
    render(<EpaOverviewRibbon workspace={state} digits={2} />);
    expect(within(card("Meteorology")).getByText("screening default", { selector: "span" })).toBeInTheDocument();
  });
});
