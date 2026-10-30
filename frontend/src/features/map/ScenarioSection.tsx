import { useState } from "react";

import { ScenarioView } from "../../components/ui/ScenarioView";
import type { Facility, WorstCaseScenario } from "../../types/workspace";

const keyOf = (s: WorstCaseScenario) => `${s.pathway_key}|${s.quantity}`;

/** The facility's worst-case scenarios: a switch between results and the chosen one in full. */
export function ScenarioSection({ facility, digits }: { facility: Facility; digits: number }) {
  const [chosen, setChosen] = useState<string | null>(null);
  const { scenarios } = facility;
  const shown = scenarios.find((s) => keyOf(s) === chosen) ?? scenarios[0];
  if (!shown) return null;
  return (
    <div className="grid gap-2">
      {scenarios.length > 1 && (
        <div role="group" aria-label="Result shown" className="inline-flex flex-wrap gap-1 text-[11px]">
          {scenarios.map((s) => (
            <button
              key={keyOf(s)}
              type="button"
              aria-pressed={keyOf(s) === keyOf(shown)}
              title={s.pathway}
              onClick={() => setChosen(keyOf(s))}
              className={`spring rounded-full px-2 py-0.5 ${keyOf(s) === keyOf(shown) ? "bg-solid font-medium text-fg shadow-sm" : "bg-fg2/10 text-fg2 hover:text-fg"}`}
            >
              {s.pathway_key.startsWith("worker") ? "Worker " : ""}
              {s.quantity_label}
            </button>
          ))}
        </div>
      )}
      <ScenarioView scenario={shown} digits={digits} />
    </div>
  );
}
