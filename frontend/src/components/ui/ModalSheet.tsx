import { useEffect, useId, useRef, type ReactNode } from "react";

import { GlassCard } from "./GlassCard";

interface ModalSheetProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

const FOCUSABLE = 'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])';

/** A macOS-style sheet: focus is trapped inside, Escape closes, focus returns on close. */
export function ModalSheet({ open, title, onClose, children }: ModalSheetProps) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);

  useEffect(() => {
    close.current = onClose;
  });

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const items = () => Array.from(panel.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []);
    items()[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        close.current();
        return;
      }
      if (event.key !== "Tab") return;
      const list = items();
      const first = list[0];
      const last = list[list.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [open]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <GlassCard
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="sheet-in w-full max-w-md p-6 shadow-[var(--shadow)]"
      >
        <h2 id={titleId} className="mb-4 text-lg font-semibold tracking-tight">
          {title}
        </h2>
        {children}
      </GlassCard>
    </div>
  );
}
