import { describe, expect, it } from "vitest";

import {
  NOT_REPORTED,
  formatCost,
  formatCount,
  formatDuration,
  formatOutcome,
  formatStarted,
  formatTokens,
  formatUsd,
} from "./format";

describe("counts and tokens", () => {
  it("groups thousands and never turns an absent count into 0", () => {
    expect(formatCount(23425)).toBe("23,425");
    expect(formatCount(0)).toBe("0");
    expect(formatCount(null)).toBe(NOT_REPORTED);
  });

  it("writes input and output tokens, and says which one is missing", () => {
    expect(formatTokens(23425, 88)).toBe("23,425 in / 88 out");
    expect(formatTokens(10, null)).toBe(`10 in / ${NOT_REPORTED} out`);
    expect(formatTokens(null, null)).toBe(NOT_REPORTED);
  });
});

describe("duration", () => {
  it.each([
    [420, "420 ms"],
    [8707, "8.7 s"],
    [125000, "2 min 5 s"],
    [60000, "1 min 0 s"],
  ])("%i ms reads %s", (ms, text) => {
    expect(formatDuration(ms)).toBe(text);
  });

  it("does not invent one", () => {
    expect(formatDuration(null)).toBe(NOT_REPORTED);
  });
});

describe("cost", () => {
  it("uses four decimals under a dollar and two above", () => {
    expect(formatUsd(0.030850000000000002)).toBe("$0.0309");
    expect(formatUsd(1.236)).toBe("$1.24");
  });

  it("marks an estimate and a lower bound differently", () => {
    expect(formatCost({ cost_usd: 0.5, cost_status: "estimate" })).toBe("~$0.5000");
    expect(formatCost({ cost_usd: 0.5, cost_status: "lower_bound" })).toBe("≥ $0.5000");
  });

  it("never prints an amount for an unpriced, unknown or absent cost", () => {
    expect(formatCost({ cost_usd: null, cost_status: "unpriced" })).toBe("unpriced");
    expect(formatCost({ cost_usd: 0.5, cost_status: "unknown" })).toBe(NOT_REPORTED);
    expect(formatCost({ cost_usd: null, cost_status: "estimate" })).toBe(NOT_REPORTED);
  });
});

describe("times and outcomes", () => {
  it("formats a recorded time and rejects a bad one", () => {
    expect(formatStarted("2026-01-02T03:04:05+00:00")).toMatch(/2026|Jan/);
    expect(formatStarted("yesterday")).toBe(NOT_REPORTED);
  });

  it("names outcomes in words", () => {
    expect(formatOutcome("ok")).toBe("Completed");
    expect(formatOutcome("error")).toBe("Failed");
    expect(formatOutcome("unknown")).toBe("Unknown");
  });
});
