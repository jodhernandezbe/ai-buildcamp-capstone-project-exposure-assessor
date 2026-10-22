import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRef } from "react";

import { useFocusTrap } from "./useFocusTrap";

function Probe({ active, onClose }: { active: boolean; onClose: () => void }) {
  const box = useRef<HTMLDivElement>(null);
  useFocusTrap(active, box, onClose);
  return (
    <>
      <button type="button">outside</button>
      <div ref={box}>
        <button type="button">first</button>
        <button type="button">last</button>
      </div>
    </>
  );
}

describe("useFocusTrap", () => {
  it("focuses the first control and wraps Tab in both directions", async () => {
    const user = userEvent.setup();
    render(<Probe active onClose={() => undefined} />);
    expect(screen.getByRole("button", { name: "first" })).toHaveFocus();
    await user.tab({ shift: true });
    expect(screen.getByRole("button", { name: "last" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "first" })).toHaveFocus();
  });

  it("closes on Escape and keeps the event from reaching the window", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const reached = vi.fn();
    window.addEventListener("keydown", reached);
    render(<Probe active onClose={onClose} />);
    await user.keyboard("{Escape}");
    window.removeEventListener("keydown", reached);
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(reached).not.toHaveBeenCalled();
  });

  it("returns focus to the previous element when it deactivates", () => {
    const { rerender } = render(<Probe active={false} onClose={() => undefined} />);
    screen.getByRole("button", { name: "outside" }).focus();
    rerender(<Probe active onClose={() => undefined} />);
    expect(screen.getByRole("button", { name: "first" })).toHaveFocus();
    rerender(<Probe active={false} onClose={() => undefined} />);
    expect(screen.getByRole("button", { name: "outside" })).toHaveFocus();
  });
});
