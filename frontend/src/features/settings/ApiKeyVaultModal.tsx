import { useState, type FormEvent } from "react";

import { ModalSheet } from "../../components/ui/ModalSheet";
import type { KeyName, KeysStatusResponse } from "../../types/workspace";

interface KeySection {
  name: KeyName;
  label: string;
  purpose: string;
  /** What is unavailable while this optional key is missing; absent for the required key. */
  missing?: string;
}

const SECTIONS: KeySection[] = [
  { name: "openai", label: "OpenAI", purpose: "Runs the assistant. Required." },
  {
    name: "census",
    label: "Census",
    purpose: "Counts the people living around a facility.",
    missing: "Without it, population counts fall back to a generic screening default.",
  },
  {
    name: "comptox",
    label: "CompTox",
    purpose: "Looks up chemical properties and toxicity benchmarks.",
    missing: "Without it, chemical properties and toxicity values cannot be looked up.",
  },
];

interface ApiKeyVaultModalProps {
  open: boolean;
  statuses: KeysStatusResponse | null;
  busy: KeyName | null;
  error: string | null;
  onSave: (name: KeyName, key: string) => Promise<boolean>;
  onClear: (name: KeyName) => Promise<boolean>;
  onClose: () => void;
}

const EMPTY: Record<KeyName, string> = { openai: "", census: "", comptox: "" };

interface SectionProps {
  section: KeySection;
  status: KeysStatusResponse[KeyName] | undefined;
  draft: string;
  busy: boolean;
  onDraft: (value: string) => void;
  onSave: () => void;
  onClear: () => void;
}

function KeySectionForm({ section, status, draft, busy, onDraft, onSave, onClear }: SectionProps) {
  const configured = status?.configured === true;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSave();
  };
  return (
    <section aria-label={`${section.label} API key`} className="border-t border-hairline pt-4 first:border-t-0 first:pt-0">
      <form onSubmit={submit} className="flex flex-col gap-3">
        <div>
          <h3 className="text-[15px] font-medium">{section.label} API key</h3>
          <p className="text-xs text-fg2">{section.purpose}</p>
        </div>
        <p
          role="status"
          className={`rounded-xl border border-hairline px-3 py-2 text-sm ${configured ? "text-ok" : "text-fg2"}`}
        >
          {configured
            ? "Key stored securely in OS Keychain"
            : "No key configured"}
        </p>
        {!configured && section.missing ? <p className="text-xs text-fg2">{section.missing}</p> : null}
        <input
          type="password"
          name={`${section.name}-api-key`}
          aria-label={`${section.label} API key`}
          autoComplete="off"
          spellCheck={false}
          value={draft}
          onChange={(event) => onDraft(event.target.value)}
          placeholder="Paste key"
          className="rounded-xl border border-hairline bg-transparent px-3 py-2 text-[15px] outline-none focus:border-accent"
        />
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            aria-label={`Clear ${section.label} key`}
            disabled={busy || !configured}
            onClick={onClear}
            className="rounded-full px-3 py-1.5 text-sm text-bad transition disabled:opacity-30"
          >
            Clear key
          </button>
          <button
            type="submit"
            aria-label={`Save ${section.label} key`}
            disabled={busy || draft.trim().length === 0}
            className="rounded-full bg-accent px-4 py-1.5 text-sm font-medium text-accent-fg transition disabled:opacity-30"
          >
            Save
          </button>
        </div>
      </form>
    </section>
  );
}

/** Store or clear the API keys in the OS keychain. No key is kept in the browser. */
export function ApiKeyVaultModal({
  open,
  statuses,
  busy,
  error,
  onSave,
  onClear,
  onClose,
}: ApiKeyVaultModalProps) {
  const [drafts, setDrafts] = useState<Record<KeyName, string>>(EMPTY);

  const close = () => {
    setDrafts(EMPTY);
    onClose();
  };
  const save = async (name: KeyName) => {
    const value = drafts[name];
    setDrafts((current) => ({ ...current, [name]: "" }));
    if (value.trim()) await onSave(name, value);
  };

  return (
    <ModalSheet open={open} title="API keys" onClose={close}>
      <div className="flex max-h-[70dvh] flex-col gap-4 overflow-y-auto pr-1">
        {SECTIONS.map((section) => (
          <KeySectionForm
            key={section.name}
            section={section}
            status={statuses?.[section.name]}
            draft={drafts[section.name]}
            busy={busy !== null}
            onDraft={(value) => setDrafts((current) => ({ ...current, [section.name]: value }))}
            onSave={() => void save(section.name)}
            onClear={() => void onClear(section.name)}
          />
        ))}
      </div>
      {error ? (
        <p role="alert" className="mt-3 text-sm text-bad">
          {error}
        </p>
      ) : null}
      <div className="mt-4 flex justify-end">
        <button type="button" onClick={close} className="rounded-full px-3 py-1.5 text-sm text-fg2">
          Done
        </button>
      </div>
    </ModalSheet>
  );
}
