import type { ConfirmationAnswers, EntryAnswer, MissingValue } from "../../types/workspace";

/** What the user has entered for one missing value so far. */
export interface EntryDraft {
  decision: "supply" | "decline" | null;
  number: string;
  unit: string;
}

export const emptyDraft = (entry: MissingValue): EntryDraft => ({
  decision: null,
  number: "",
  unit: entry.accepted_units[0] ?? "",
});

/** A number the browser can send: finite and written as a plain number (no text, no empties). */
export function parseNumber(text: string): number | null {
  if (text.trim() === "") return null;
  const value = Number(text);
  return Number.isFinite(value) ? value : null;
}

/** Whether one entry has a complete answer. A supplied value still needs a number and a unit. */
export function isAnswered(draft: EntryDraft): boolean {
  if (draft.decision === "decline") return true;
  if (draft.decision !== "supply") return false;
  return parseNumber(draft.number) !== null && draft.unit !== "";
}

/** The answers in the wire shape, one per entry, in the order the request lists them. */
export function toAnswers(
  requestId: string,
  entries: MissingValue[],
  drafts: Record<string, EntryDraft>,
): ConfirmationAnswers | null {
  const [first, ...rest] = entries.map((entry): EntryAnswer => {
    const draft = drafts[entry.entry_id] ?? emptyDraft(entry);
    if (draft.decision === "supply") {
      return {
        entry_id: entry.entry_id,
        decision: "supply",
        number: parseNumber(draft.number),
        unit: draft.unit,
      };
    }
    return { entry_id: entry.entry_id, decision: "decline" };
  });
  if (first === undefined) return null;
  return { request_id: requestId, entries: [first, ...rest] };
}

/** One line of the transcript that says what was answered, in words. */
export function summarize(entries: MissingValue[], drafts: Record<string, EntryDraft>): string {
  const parts = entries.map((entry) => {
    const draft = drafts[entry.entry_id] ?? emptyDraft(entry);
    const subject = `${entry.quantity} for ${entry.subject}`;
    if (draft.decision === "supply") return `${subject} = ${draft.number} ${draft.unit}`;
    return `proceed without ${subject}`;
  });
  return `Answers: ${parts.join("; ")}.`;
}
