import type { UsageTotals } from "../../types/workspace";
import { formatCost, formatTokens, formatUsd, totalTokens } from "./formatUsage";

const totals = (over: Partial<UsageTotals> = {}): UsageTotals => ({
  calls: 2,
  input_tokens: 1000,
  cached_input_tokens: 0,
  output_tokens: 200,
  complete: true,
  cost_usd: 0.0123,
  cost_status: "estimate",
  priced_on: "2026-10-20",
  ...over,
});

describe("formatUsage", () => {
  it("shortens token counts", () => {
    expect(formatTokens(950)).toBe("950");
    expect(formatTokens(12345)).toBe("12.3K");
  });

  it("keeps the precision small amounts need", () => {
    expect(formatUsd(0.0123)).toBe("$0.0123");
    expect(formatUsd(0.0004)).toBe("$0.0004");
    expect(formatUsd(0.4567)).toBe("$0.4567");
    expect(formatUsd(1)).toBe("$1.00");
    expect(formatUsd(1.236)).toBe("$1.24");
  });

  it("marks an estimate, a lower bound and an unpriced model differently", () => {
    expect(formatCost(totals())).toBe("~$0.0123");
    expect(formatCost(totals({ cost_status: "lower_bound" }))).toBe("≥ $0.0123");
    expect(formatCost(totals({ cost_usd: null, cost_status: "unpriced" }))).toBe("unpriced");
  });

  it("never shows a dollar amount the server did not give", () => {
    expect(formatCost(totals({ cost_usd: null, cost_status: "estimate" }))).toBe("unpriced");
  });

  it("adds input and output tokens", () => {
    expect(totalTokens(totals())).toBe(1200);
  });
});
