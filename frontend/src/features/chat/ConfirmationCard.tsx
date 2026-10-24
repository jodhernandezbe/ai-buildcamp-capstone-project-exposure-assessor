import { useState } from "react";

import type { ConfirmationAnswers, ConfirmationPrompt, MissingValue } from "../../types/workspace";
import {
  emptyDraft,
  isAnswered,
  parseNumber,
  summarize,
  toAnswers,
  type EntryDraft,
} from "./confirmation";

interface ConfirmationCardProps {
  prompt: ConfirmationPrompt;
  busy: boolean;
  onConfirm: (answers: ConfirmationAnswers, summary: string) => void;
}

/** A value's label and what it is needed for, e.g. "iur for 71-43-2". */
function heading(entry: MissingValue): string {
  return `${entry.quantity} for ${entry.subject}`;
}

/** The value's plausible range, in its target unit (the first accepted unit). */
function rangeText(entry: MissingValue): string {
  const target = entry.accepted_units[0] ?? "";
  return `plausible range ${entry.minimum.toPrecision(2)} to ${entry.maximum.toPrecision(2)} ${target}`;
}

interface EntryRowProps {
  entry: MissingValue;
  draft: EntryDraft;
  onChange: (draft: EntryDraft) => void;
}

function EntryRow({ entry, draft, onChange }: EntryRowProps) {
  const id = `value-${entry.entry_id}`;
  const number = parseNumber(draft.number);
  const invalid = draft.decision === "supply" && draft.number !== "" && number === null;
  return (
    <fieldset className="space-y-2 border-t border-white/10 pt-3 first:border-t-0 first:pt-0">
      <legend className="text-sm font-medium">{heading(entry)}</legend>
      <p className="text-xs text-fg2">{entry.purpose}. {rangeText(entry)}.</p>
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor={`${id}-number`} className="sr-only">
          Value for {heading(entry)}
        </label>
        <input
          id={`${id}-number`}
          type="number"
          inputMode="decimal"
          step="any"
          aria-invalid={invalid}
          value={draft.number}
          disabled={draft.decision === "decline"}
          onChange={(event) =>
            onChange({ ...draft, decision: "supply", number: event.target.value })
          }
          className="w-32 rounded-lg bg-white/5 px-2 py-1 text-sm outline-none disabled:opacity-40"
        />
        <label htmlFor={`${id}-unit`} className="sr-only">
          Unit for {heading(entry)}
        </label>
        <select
          id={`${id}-unit`}
          value={draft.unit}
          disabled={draft.decision === "decline"}
          onChange={(event) => onChange({ ...draft, unit: event.target.value })}
          className="rounded-lg bg-white/5 px-2 py-1 text-sm outline-none disabled:opacity-40"
        >
          {entry.accepted_units.map((unit) => (
            <option key={unit} value={unit}>
              {unit}
            </option>
          ))}
        </select>
        <button
          type="button"
          aria-pressed={draft.decision === "decline"}
          onClick={() =>
            onChange({ ...draft, decision: draft.decision === "decline" ? null : "decline" })
          }
          className="rounded-full px-3 py-1 text-xs underline"
        >
          Proceed without
        </button>
      </div>
      {invalid ? <p className="text-xs text-red-300">Enter a number.</p> : null}
    </fieldset>
  );
}

/** The request for missing values, shown in the chat thread with one row per value. */
export function ConfirmationCard({ prompt, busy, onConfirm }: ConfirmationCardProps) {
  const [drafts, setDrafts] = useState<Record<string, EntryDraft>>({});
  const ready = prompt.entries.every((entry) =>
    isAnswered(drafts[entry.entry_id] ?? emptyDraft(entry)),
  );
  const draftOf = (entry: MissingValue) => drafts[entry.entry_id] ?? emptyDraft(entry);
  const setDraft = (entry: MissingValue, draft: EntryDraft) =>
    setDrafts((current) => ({ ...current, [entry.entry_id]: draft }));
  const confirm = () => {
    const answers = toAnswers(prompt.request_id, prompt.entries, drafts);
    if (answers) onConfirm(answers, summarize(prompt.entries, drafts));
  };

  return (
    <section aria-label="Values the assessment needs" className="glass mx-4 mb-2 space-y-3 rounded-2xl p-4">
      <p className="text-sm">
        The assessment could not find these values. Enter one, or proceed without it.
      </p>
      {prompt.entries.map((entry) => (
        <EntryRow
          key={entry.entry_id}
          entry={entry}
          draft={draftOf(entry)}
          onChange={(draft) => setDraft(entry, draft)}
        />
      ))}
      <button
        type="button"
        disabled={!ready || busy}
        onClick={() => confirm()}
        className="spring rounded-full bg-accent px-4 py-1.5 text-sm text-accent-fg transition disabled:opacity-30"
      >
        Confirm
      </button>
    </section>
  );
}
