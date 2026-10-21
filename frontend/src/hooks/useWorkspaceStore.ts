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

/** The workspace the left pane shows: the latest `workspace_update`, empty before any. */
export function useWorkspaceStore() {
  const [workspace, setWorkspace] = useState<WorkspaceState>(EMPTY_WORKSPACE);
  const apply = useCallback((state: WorkspaceState) => setWorkspace(state), []);
  const clear = useCallback(() => setWorkspace(EMPTY_WORKSPACE), []);
  return { workspace, apply, clear };
}
