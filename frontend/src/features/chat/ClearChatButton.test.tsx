import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ClearChatButton } from "./ClearChatButton";

describe("ClearChatButton", () => {
  it("clears the chat when clicked", async () => {
    const user = userEvent.setup();
    const onClear = vi.fn();
    render(<ClearChatButton disabled={false} onClear={onClear} />);
    await user.click(screen.getByRole("button", { name: "Clear chat" }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("does nothing while disabled", async () => {
    const user = userEvent.setup();
    const onClear = vi.fn();
    render(<ClearChatButton disabled onClear={onClear} />);
    const button = screen.getByRole("button", { name: "Clear chat" });
    expect(button).toBeDisabled();
    await user.click(button);
    expect(onClear).not.toHaveBeenCalled();
  });
});
