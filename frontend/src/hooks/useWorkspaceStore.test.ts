import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { facility } from "../test/fixtures";
import type { WorkspaceState } from "../types/workspace";
import { EMPTY_WORKSPACE, useWorkspaceStore, withDefaults } from "./useWorkspaceStore";

/** The object without the named keys. */
const without = <T extends object>(value: T, keys: string[]) =>
  Object.fromEntries(Object.entries(value).filter(([key]) => !keys.includes(key)));

/** What a server that predates the worker fields sends. */
function older(): WorkspaceState {
  const plain = without(facility(), [
    "occupational_exposure",
    "operational_profile",
    "fugitive_release_kg_per_year",
    "fugitive_reporting_year",
  ]);
  return { ...without(EMPTY_WORKSPACE, ["worker_risk"]), facilities: [plain] } as unknown as WorkspaceState;
}

describe("withDefaults", () => {
  it("fills the worker fields an older server does not send, so nothing reads undefined", () => {
    const filled = withDefaults(older());
    expect(filled.worker_risk).toEqual(EMPTY_WORKSPACE.worker_risk);
    expect(filled.facilities[0]?.occupational_exposure).toBeNull();
    expect(filled.facilities[0]?.operational_profile).toBeNull();
    expect(filled.facilities[0]?.fugitive_release_kg_per_year).toBeNull();
  });

  it("keeps what the server did send", () => {
    const sent = { ...EMPTY_WORKSPACE, worker_risk: { ...EMPTY_WORKSPACE.worker_risk, reason: "x" } };
    expect(withDefaults(sent).worker_risk.reason).toBe("x");
  });
});

describe("useWorkspaceStore", () => {
  it("applies and replaces with the defaults filled", () => {
    const { result } = renderHook(() => useWorkspaceStore());
    act(() => result.current.apply(older()));
    expect(result.current.workspace.worker_risk).toEqual(EMPTY_WORKSPACE.worker_risk);
    act(() => result.current.replace(older()));
    expect(result.current.workspace.facilities[0]?.occupational_exposure).toBeNull();
  });
});
