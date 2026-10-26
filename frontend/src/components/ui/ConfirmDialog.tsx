import { useId, useRef, type ReactNode } from "react";

import { useFocusTrap } from "./useFocusTrap";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  /** What will happen, in words. */
  children: ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  /** The action cannot be undone: the confirm button reads as destructive. */
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * An in-page confirmation over a scrim (never a browser dialog). Focus starts on Cancel, Tab
 * stays inside, Escape or the scrim cancels, and focus returns to the opener on close.
 */
export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  cancelLabel = "Cancel",
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId();
  const bodyId = useId();
  const panel = useRef<HTMLElement>(null);
  useFocusTrap(open, panel, onCancel);
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4"
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) onCancel();
      }}
    >
      <section
        ref={panel}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
        className="sheet-in flex w-full max-w-sm flex-col gap-3 rounded-2xl border border-hairline bg-solid p-5 shadow-[var(--shadow)]"
      >
        <h2 id={titleId} className="text-lg font-semibold tracking-tight">
          {title}
        </h2>
        <div id={bodyId} className="flex flex-col gap-2 text-sm text-fg2">
          {children}
        </div>
        <div className="mt-2 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="spring rounded-xl bg-hairline px-4 py-2 text-sm font-semibold transition hover:opacity-80"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`spring rounded-xl border px-4 py-2 text-sm font-semibold transition hover:bg-hairline ${
              destructive ? "border-bad text-bad" : "border-accent text-accent"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}
