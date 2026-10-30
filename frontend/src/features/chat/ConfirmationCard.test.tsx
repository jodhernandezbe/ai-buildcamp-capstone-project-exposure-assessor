import userEvent from "@testing-library/user-event";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ConfirmationPrompt, MissingValue } from "../../types/workspace";
import { ConfirmationCard } from "./ConfirmationCard";

const iur: MissingValue = {
  entry_id: "iur:71-43-2",
  quantity: "iur",
  subject: "71-43-2",
  accepted_units: ["1/(ug/m^3)", "1/(mg/m^3)"],
  minimum: 1e-9,
  maximum: 1000,
  purpose: "the cancer risk",
};

const rfc: MissingValue = {
  entry_id: "rfc:71-43-2",
  quantity: "rfc",
  subject: "71-43-2",
  accepted_units: ["mg/m^3", "ug/m^3"],
  minimum: 1e-8,
  maximum: 1000,
  purpose: "the hazard quotient",
};

const prompt: ConfirmationPrompt = { request_id: "req1", entries: [iur, rfc] };

function declineButton(index: number): HTMLElement {
  const button = screen.getAllByRole("button", { name: "Proceed without" })[index];
  if (!button) throw new Error(`no "Proceed without" button ${index}`);
  return button;
}

function setup(onConfirm = vi.fn()) {
  render(<ConfirmationCard prompt={prompt} busy={false} onConfirm={onConfirm} />);
  return onConfirm;
}

describe("ConfirmationCard", () => {
  it("shows each value with its purpose, range and the units it accepts", () => {
    setup();
    expect(screen.getByText("inhalation unit risk for 71-43-2")).toBeInTheDocument();
    expect(screen.getByText(/the cancer risk/)).toBeInTheDocument();
    expect(screen.getAllByRole("combobox")[0]).toHaveDisplayValue("1/(ug/m^3)");
    expect(screen.getAllByRole("option", { name: "1/(mg/m^3)" })).toHaveLength(1);
  });

  it("lets the user type a value straight into an unanswered field", async () => {
    const user = userEvent.setup();
    setup();
    const field = screen.getByRole("spinbutton", { name: /Value for inhalation unit risk for 71-43-2/ });
    await user.type(field, "0.5");
    expect(field).toHaveValue(0.5);
  });

  it("keeps Confirm disabled until every value is answered", () => {
    setup();
    const confirm = screen.getByRole("button", { name: "Confirm" });
    expect(confirm).toBeDisabled();
    fireEvent.click(declineButton(0));
    expect(confirm).toBeDisabled();
    fireEvent.click(declineButton(1));
    expect(confirm).toBeEnabled();
  });

  it("sends a supplied value in the chosen unit and a declined one as declined", () => {
    const onConfirm = setup();
    fireEvent.change(screen.getByLabelText("Value for inhalation unit risk for 71-43-2"), {
      target: { value: "0.002" },
    });
    fireEvent.change(screen.getByLabelText("Unit for inhalation unit risk for 71-43-2"), {
      target: { value: "1/(mg/m^3)" },
    });
    fireEvent.click(declineButton(1));
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    const [answers, summary] = onConfirm.mock.calls[0] ?? [];
    expect(answers).toEqual({
      request_id: "req1",
      entries: [
        { entry_id: "iur:71-43-2", decision: "supply", number: 0.002, unit: "1/(mg/m^3)" },
        { entry_id: "rfc:71-43-2", decision: "decline" },
      ],
    });
    expect(summary).toBe("Answers: iur for 71-43-2 = 0.002 1/(mg/m^3); proceed without rfc for 71-43-2.");
  });

  it("does not accept text that is not a number", () => {
    setup();
    fireEvent.change(screen.getByLabelText("Value for inhalation unit risk for 71-43-2"), {
      target: { value: "" },
    });
    fireEvent.click(declineButton(1));
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
  });

  it("is disabled while a turn is running", () => {
    render(<ConfirmationCard prompt={prompt} busy onConfirm={vi.fn()} />);
    fireEvent.click(declineButton(0));
    fireEvent.click(declineButton(1));
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
  });
});
