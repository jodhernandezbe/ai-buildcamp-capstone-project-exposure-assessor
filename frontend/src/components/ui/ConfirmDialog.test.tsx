import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { ConfirmDialog } from "./ConfirmDialog";

function Probe({ onConfirm }: { onConfirm: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        open
      </button>
      <ConfirmDialog
        open={open}
        title="Clear this workspace?"
        confirmLabel="Clear"
        destructive
        onConfirm={() => {
          onConfirm();
          setOpen(false);
        }}
        onCancel={() => setOpen(false)}
      >
        <p>It cannot be recovered.</p>
      </ConfirmDialog>
    </>
  );
}

describe("ConfirmDialog", () => {
  it("renders nothing while closed", () => {
    render(<Probe onConfirm={() => undefined} />);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("is a named, described modal with focus on Cancel", async () => {
    const user = userEvent.setup();
    render(<Probe onConfirm={() => undefined} />);
    await user.click(screen.getByRole("button", { name: "open" }));
    const dialog = screen.getByRole("alertdialog", { name: "Clear this workspace?" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAccessibleDescription("It cannot be recovered.");
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
  });

  it("Escape cancels and returns focus to the opener", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(<Probe onConfirm={onConfirm} />);
    await user.click(screen.getByRole("button", { name: "open" }));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "open" })).toHaveFocus();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("confirms once", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(<Probe onConfirm={onConfirm} />);
    await user.click(screen.getByRole("button", { name: "open" }));
    await user.click(screen.getByRole("button", { name: "Clear" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });
});
