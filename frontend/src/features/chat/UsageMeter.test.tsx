import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Usage, UsageTotals } from "../../types/workspace";
import { UsageMeter } from "./UsageMeter";

const totals = (over: Partial<UsageTotals> = {}): UsageTotals => ({
  calls: 3,
  input_tokens: 12000,
  cached_input_tokens: 4000,
  output_tokens: 345,
  complete: true,
  cost_usd: 0.0456,
  cost_status: "estimate",
  priced_on: "2026-10-20",
  ...over,
});

const usage = (session: Partial<UsageTotals> = {}, turn: Partial<UsageTotals> = {}): Usage => ({
  type: "usage",
  seq: 9,
  turn: totals({ calls: 1, input_tokens: 100, output_tokens: 20, cost_usd: 0.001, ...turn }),
  session: totals(session),
});

describe("UsageMeter", () => {
  it("shows nothing before the first turn", () => {
    const { container } = render(<UsageMeter usage={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the session's tokens and estimated cost", () => {
    render(<UsageMeter usage={usage()} />);
    expect(screen.getByRole("button", { name: "Usage: 12.3K tokens, ~$0.0456" })).toBeInTheDocument();
  });

  it("shows tokens and 'unpriced' instead of a dollar amount without a price", () => {
    render(<UsageMeter usage={usage({ cost_usd: null, cost_status: "unpriced", priced_on: null })} />);
    expect(screen.getByRole("button")).toHaveTextContent("unpriced");
    expect(screen.getByRole("button")).not.toHaveTextContent("$");
  });

  it("opens a breakdown of the last turn and the session", async () => {
    const user = userEvent.setup();
    render(<UsageMeter usage={usage()} />);
    await user.click(screen.getByRole("button"));
    const panel = screen.getByRole("region", { name: "Usage breakdown" });
    expect(panel).toHaveTextContent("Estimated from list prices (priced 2026-10-20).");
    expect(screen.getByRole("region", { name: "Session" })).toHaveTextContent("12,000");
    expect(screen.getByRole("region", { name: "Session" })).toHaveTextContent("4,000");
    expect(screen.getByRole("region", { name: "Last turn" })).toHaveTextContent("100");
  });

  it("says when the totals are a minimum or the model has no price", async () => {
    const user = userEvent.setup();
    const partial = usage({ complete: false, cost_status: "lower_bound" });
    const { rerender } = render(<UsageMeter usage={partial} />);
    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("region", { name: "Usage breakdown" })).toHaveTextContent("minimum");
    expect(screen.getByRole("button", { name: /≥ \$0.0456/ })).toBeInTheDocument();
    rerender(<UsageMeter usage={usage({ cost_usd: null, cost_status: "unpriced" })} />);
    expect(screen.getByRole("region", { name: "Usage breakdown" })).toHaveTextContent(
      "No price is configured",
    );
  });

  it("updates when a new usage event arrives", () => {
    const { rerender } = render(<UsageMeter usage={usage()} />);
    rerender(<UsageMeter usage={usage({ input_tokens: 50000, output_tokens: 0, cost_usd: 0.2 })} />);
    expect(screen.getByRole("button")).toHaveTextContent("50K tokens");
    expect(screen.getByRole("button")).toHaveTextContent("~$0.2000");
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    render(<UsageMeter usage={usage()} />);
    await user.click(screen.getByRole("button"));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("region", { name: "Usage breakdown" })).toBeNull();
  });
});
