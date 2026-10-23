import type { Facility } from "../../types/workspace";

/** What became of a facility in the assessment; "not_assessed" when nothing was computed. */
export type Outcome =
  | "full"
  | "worst_case_only"
  | "screened_out_at_bound"
  | "screened_out_with_own_stacks"
  | "not_assessed";

/** The facility's outcome, as the batch screening reported it (else from whether it has a result). */
export function outcomeOf(facility: Facility): Outcome {
  if (facility.screening) return facility.screening.outcome;
  return facility.exposure ? "full" : "not_assessed";
}

/** Whether the facility has a worst-case result of its own (not a screening bound). */
export const isAssessed = (facility: Facility): boolean => {
  const outcome = outcomeOf(facility);
  return outcome === "full" || outcome === "worst_case_only";
};

/** Whether the facility was left out of the full assessment by the screen. */
export const isScreenedOut = (facility: Facility): boolean => outcomeOf(facility).startsWith("screened_out");
