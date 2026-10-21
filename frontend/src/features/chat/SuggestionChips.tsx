interface SuggestionChipsProps {
  suggestions: string[];
  disabled: boolean;
  onPick: (text: string) => void;
}

/** Onboarding prompts: one click sends the suggestion as the user's message. */
export function SuggestionChips({ suggestions, disabled, onPick }: SuggestionChipsProps) {
  if (suggestions.length === 0) return null;
  return (
    <ul aria-label="Suggestions" className="mt-6 flex flex-col gap-2">
      {suggestions.map((text) => (
        <li key={text}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(text)}
            className="glass spring w-full rounded-2xl px-4 py-3 text-left text-sm transition hover:bg-hairline disabled:opacity-40"
          >
            {text}
          </button>
        </li>
      ))}
    </ul>
  );
}
