import { describe, expect, it } from "vitest";

import type { MissingValue } from "../../types/workspace";
import { isAnswered, parseNumber, summarize, toAnswers, type EntryDraft } from "./confirmation";

const entry: MissingValue = {
  entry_id: "iur:A",
  quantity: "iur",
  subject: "A",
  accepted_units: ["1/(ug/m^3)"],
  minimum: 1e-9,
  maximum: 1000,
  purpose: "the cancer risk",
};

const supply = (number: string): EntryDraft => ({ decision: "supply", number, unit: "1/(ug/m^3)" });

describe("parseNumber", () => {
  it("accepts plain numbers and rejects empty, text and non-finite input", () => {
    expect(parseNumber("2e-6")).toBe(2e-6);
    expect(parseNumber(" 12 ")).toBe(12);
    expect(parseNumber("")).toBeNull();
    expect(parseNumber("abc")).toBeNull();
    expect(parseNumber("Infinity")).toBeNull();
  });
});

describe("isAnswered", () => {
  it("needs a decision, and a number and unit for a supplied value", () => {
    expect(isAnswered({ decision: null, number: "", unit: "x" })).toBe(false);
    expect(isAnswered({ decision: "decline", number: "", unit: "" })).toBe(true);
    expect(isAnswered(supply("1"))).toBe(true);
    expect(isAnswered(supply(""))).toBe(false);
  });
});

describe("toAnswers", () => {
  it("is null when there are no entries", () => {
    expect(toAnswers("r", [], {})).toBeNull();
  });

  it("keeps the request id and entry order", () => {
    const answers = toAnswers("r", [entry], { [entry.entry_id]: supply("3") });
    expect(answers).toEqual({
      request_id: "r",
      entries: [{ entry_id: "iur:A", decision: "supply", number: 3, unit: "1/(ug/m^3)" }],
    });
  });
});

describe("summarize", () => {
  it("writes the answer in words for the transcript", () => {
    expect(summarize([entry], { [entry.entry_id]: supply("3") })).toBe(
      "Answers: iur for A = 3 1/(ug/m^3).",
    );
  });
});
