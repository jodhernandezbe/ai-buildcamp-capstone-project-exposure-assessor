import { useEffect, useRef, type RefObject } from "react";

const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])';

/**
 * While `active`, keeps Tab inside `container`, closes on Escape (marking the event handled so
 * layers below ignore it) and returns focus to the element that had it on close.
 */
export function useFocusTrap(
  active: boolean,
  container: RefObject<HTMLElement | null>,
  onClose: () => void,
): void {
  const close = useRef(onClose);
  useEffect(() => {
    close.current = onClose;
  });

  useEffect(() => {
    if (!active) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const items = () => Array.from(container.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []);
    items()[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
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
  }, [active, container]);
}
