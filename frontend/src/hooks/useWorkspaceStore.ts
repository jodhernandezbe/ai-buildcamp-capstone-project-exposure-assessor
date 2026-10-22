import { useCallback, useState } from "react";

import type { WorkspaceState } from "../types/workspace";

/** What the server sends before any tool has run (nothing placed, nothing computed). */
export const EMPTY_WORKSPACE: WorkspaceState = {
  framing_version: 0,
  bounds: null,
  facilities: [],
  selected_frs_id: null,
  chemical: {
    cas_number: null,
    molecular_weight_g_mol: null,
    rfc_mg_m3: null,
    iur_per_ug_m3: null,
    sources: {},
    read_across: {
      kind: "not_evaluated",
      surrogate_cas: null,
      surrogate_name: null,
      hybrid_score: null,
      cosine_similarity: null,
      tanimoto_similarity: null,
      within_applicability_domain: null,
      warnings: [],
    },
    warnings: [],
  },
  risk: {
    hq_worst: null,
    cancer_risk_worst: null,
    hq_representative: null,
    cancer_risk_representative: null,
    reason: "not yet computed",
  },
  receptors: null,
  meteorology: null,
  unattributed: [],
  warnings: [],
};

/**
 * The workspace the analysis area shows: the latest `workspace_update`, empty before any.
 * `epoch` rises when the whole workspace is replaced (a new or restored run), so the map
 * reframes even if the replacement carries the same framing version as the one it replaces.
 */
export function useWorkspaceStore() {
  const [workspace, setWorkspace] = useState<WorkspaceState>(EMPTY_WORKSPACE);
  const [epoch, setEpoch] = useState(0);
  const apply = useCallback((state: WorkspaceState) => setWorkspace(state), []);
  const replace = useCallback((state: WorkspaceState) => {
    setWorkspace(state);
    setEpoch((now) => now + 1);
  }, []);
  const clear = useCallback(() => replace(EMPTY_WORKSPACE), [replace]);
  return { workspace, epoch, apply, replace, clear };
}
