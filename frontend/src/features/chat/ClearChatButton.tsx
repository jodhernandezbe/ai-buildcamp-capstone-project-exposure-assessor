import { AiOutlineClear } from "react-icons/ai";

interface ClearChatButtonProps {
  /** Nothing to clear, or a reply is still streaming. */
  disabled: boolean;
  onClear: () => void;
}

/** Starts a fresh conversation; the previous run stays in the rail's history. */
export function ClearChatButton({ disabled, onClear }: ClearChatButtonProps) {
  return (
    <button
      type="button"
      aria-label="Clear chat"
      title="Clear chat"
      disabled={disabled}
      onClick={onClear}
      className="spring grid size-9 place-items-center rounded-full text-fg2 transition hover:bg-hairline hover:text-fg disabled:pointer-events-none disabled:opacity-40"
    >
      <AiOutlineClear size={18} aria-hidden="true" />
    </button>
  );
}
