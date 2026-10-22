import { TbMessageChatbot } from "react-icons/tb";

interface CopilotToggleProps {
  /** Whether the chat dock is showing; the control then hides it. */
  open: boolean;
  onToggle: () => void;
}

/** The chatbot control at the top of the workspace that shows or hides the chat dock. */
export function CopilotToggle({ open, onToggle }: CopilotToggleProps) {
  return (
    <button
      type="button"
      aria-label={open ? "Collapse copilot" : "Show copilot"}
      aria-expanded={open}
      title={open ? "Collapse copilot" : "Show copilot"}
      onClick={onToggle}
      className={`spring grid size-9 place-items-center rounded-full transition ${
        open ? "text-fg2 hover:bg-hairline hover:text-fg" : "bg-accent text-accent-fg shadow-sm hover:opacity-90"
      }`}
    >
      <TbMessageChatbot size={20} aria-hidden="true" />
    </button>
  );
}
