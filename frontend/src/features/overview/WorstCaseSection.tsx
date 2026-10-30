import { useMemo, useState } from "react";

import { ScenarioView } from "../../components/ui/ScenarioView";
import { formatNumber } from "../../lib/format";
import { ranking, scenarioFor } from "../../lib/scenarios";
import type { ScenarioDriver, WorkspaceState } from "../../types/workspace";
import { CardFrame } from "./Metric";

const same = (a: ScenarioDriver, b: ScenarioDriver | undefined) =>
  b !== undefined && a.pathway_key === b.pathway_key && a.quantity === b.quantity;

/** The drivers grouped by pathway, in the order the server listed them. */
function byPathway(drivers: ScenarioDriver[]): [string, ScenarioDriver[]][] {
  const groups = new Map<string, ScenarioDriver[]>();
  for (const driver of drivers) groups.set(driver.pathway_key, [...(groups.get(driver.pathway_key) ?? []), driver]);
  return [...groups.entries()];
}

/** The names the scenarios themselves carry, so no pathway or quantity is named here. */
function names(workspace: WorkspaceState) {
  const all = workspace.facilities.flatMap((f) => f.scenarios);
  return {
    pathway: (key: string) => all.find((s) => s.pathway_key === key)?.pathway ?? key,
    quantity: (d: ScenarioDriver) =>
      all.find((s) => s.pathway_key === d.pathway_key && s.quantity === d.quantity)?.quantity_label ?? d.quantity,
  };
}

function Choice({
  drivers,
  workspace,
  chosen,
  onChoose,
}: {
  drivers: ScenarioDriver[];
  workspace: WorkspaceState;
  chosen: ScenarioDriver | undefined;
  onChoose: (driver: ScenarioDriver) => void;
}) {
  const label = names(workspace);
  return (
    <div className="grid gap-1.5">
      {byPathway(drivers).map(([key, members]) => (
        <div key={key} role="group" aria-label={label.pathway(key)} className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-fg2">{label.pathway(key)}</span>
          <div className="inline-flex flex-wrap rounded-full bg-fg2/10 p-0.5 text-[11px]">
            {members.map((driver) => (
              <button
                key={driver.quantity}
                type="button"
                aria-pressed={same(driver, chosen)}
                onClick={() => onChoose(driver)}
                className={`spring rounded-full px-2 py-0.5 ${same(driver, chosen) ? "bg-solid font-medium text-fg shadow-sm" : "text-fg2 hover:text-fg"}`}
              >
                {label.quantity(driver)}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Others({
  workspace,
  driver,
  shown,
  digits,
  onShow,
}: {
  workspace: WorkspaceState;
  driver: ScenarioDriver;
  shown: string;
  digits: number;
  onShow: (frsId: string) => void;
}) {
  const others = ranking(workspace.facilities, driver.pathway_key, driver.quantity).filter((r) => r.frsId !== driver.frs_id);
  if (others.length === 0) return null;
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-fg2 hover:text-fg">Other facilities ({others.length})</summary>
      <ul className="m-0 mt-1 grid list-none gap-1 p-0">
        {others.map((other) => (
          <li key={other.frsId}>
            <button
              type="button"
              aria-pressed={shown === other.frsId}
              onClick={() => onShow(other.frsId)}
              className="spring flex w-full justify-between gap-2 rounded-lg bg-fg2/5 px-2 py-1 text-left hover:bg-fg2/10"
            >
              <span className="truncate">{other.name ?? `FRS ${other.frsId}`}</span>
              <span className="tabular-nums">{formatNumber(other.value, digits)}</span>
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}

/**
 * The worst-case scenarios: for each result, the facility that has the highest value and the
 * combination of factors behind it. The other facilities are one closed control away; choosing one
 * shows its own scenario of the same result, and the driver is a click back.
 */
export function WorstCaseSection({ workspace, digits }: { workspace: WorkspaceState; digits: number }) {
  const drivers = workspace.scenario_drivers;
  const [picked, setPicked] = useState<{ pathway: string; quantity: string } | null>(null);
  const [facilityId, setFacilityId] = useState<string | null>(null);
  const chosen = useMemo(
    () => drivers.find((d) => d.pathway_key === picked?.pathway && d.quantity === picked.quantity) ?? drivers[0],
    [drivers, picked],
  );
  const choose = (driver: ScenarioDriver) => {
    setPicked({ pathway: driver.pathway_key, quantity: driver.quantity });
    setFacilityId(null);
  };
  const shownId = chosen && workspace.facilities.some((f) => f.frs_id === facilityId) ? facilityId : chosen?.frs_id;
  const facility = workspace.facilities.find((f) => f.frs_id === shownId);
  const scenario = chosen && facility ? scenarioFor(facility, chosen.pathway_key, chosen.quantity) : null;
  return (
    <CardFrame title="Worst-case scenarios">
      {!chosen || !facility || !scenario ? (
        <p className="m-0 text-sm text-fg2">
          No scenario yet: assess facilities and each result will show the combination of factors that drives it.
        </p>
      ) : (
        <>
          <Choice drivers={drivers} workspace={workspace} chosen={chosen} onChoose={choose} />
          <p className="m-0 text-sm">
            <span className="font-medium">{facility.name ?? `FRS ${facility.frs_id}`}</span>
            <span className="text-fg2">{shownId === chosen.frs_id ? " · drives this result" : " · another facility"}</span>
            {shownId !== chosen.frs_id && (
              <button type="button" onClick={() => setFacilityId(null)} className="spring ml-2 text-xs text-accent underline">
                Show the facility that drives it
              </button>
            )}
          </p>
          <ScenarioView scenario={scenario} digits={digits} />
          <Others workspace={workspace} driver={chosen} shown={shownId ?? ""} digits={digits} onShow={setFacilityId} />
        </>
      )}
    </CardFrame>
  );
}
