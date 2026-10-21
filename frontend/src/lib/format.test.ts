import {
  NOT_REPORTED,
  formatCount,
  formatNumber,
  formatRange,
  formatReported,
  formatScientific,
  formatSignificant,
  formatWithUnit,
  orNotReported,
} from "./format";

describe("formatScientific", () => {
  it("writes a cancer risk of 0.000012 as 1.2 × 10⁻⁵", () => {
    expect(formatScientific(0.000012, 2)).toBe("1.2 × 10⁻⁵");
  });

  it("uses the configured significant digits", () => {
    expect(formatScientific(0.000012345, 3)).toBe("1.23 × 10⁻⁵");
    expect(formatScientific(0.000012345, 1)).toBe("1 × 10⁻⁵");
  });

  it("writes large values with a positive exponent", () => {
    expect(formatScientific(1.5e7, 2)).toBe("1.5 × 10⁷");
  });
});

describe("formatSignificant", () => {
  it("drops trailing zeros", () => {
    expect(formatSignificant(0.82, 3)).toBe("0.82");
    expect(formatSignificant(1200.4, 2)).toBe("1200");
  });
});

describe("formatNumber", () => {
  it("uses plain digits for ordinary values", () => {
    expect(formatNumber(0.8234, 2)).toBe("0.82");
    expect(formatNumber(3, 2)).toBe("3");
  });

  it("uses scientific notation for very small and very large values", () => {
    expect(formatNumber(0.000012, 2)).toBe("1.2 × 10⁻⁵");
    expect(formatNumber(2.5e6, 2)).toBe("2.5 × 10⁶");
  });

  it("shows zero as zero, not as scientific", () => {
    expect(formatNumber(0, 2)).toBe("0");
  });

  it.each([null, undefined, Number.NaN, Infinity])("shows %s as not reported", (value) => {
    expect(formatNumber(value, 2)).toBe(NOT_REPORTED);
  });
});

describe("other helpers", () => {
  it("attaches a unit only to a present value", () => {
    expect(formatWithUnit(3, "m/s", 2)).toBe("3 m/s");
    expect(formatWithUnit(null, "m/s", 2)).toBe(NOT_REPORTED);
  });

  it("groups thousands", () => {
    expect(formatCount(12345)).toBe("12,345");
    expect(formatCount(null)).toBe(NOT_REPORTED);
  });

  it("treats blank text as not reported", () => {
    expect(orNotReported("  ")).toBe(NOT_REPORTED);
    expect(orNotReported(null)).toBe(NOT_REPORTED);
    expect(orNotReported("IRIS")).toBe("IRIS");
  });
});

describe("formatRange", () => {
  it("shows one value when both ends are equal", () => {
    expect(formatRange(0.5, 0.5, 2)).toBe("0.5");
  });

  it("shows low – high otherwise", () => {
    expect(formatRange(0.2, 0.9, 2)).toBe("0.2 – 0.9");
    expect(formatRange(0.000001, 0.00002, 2)).toBe("1 × 10⁻⁶ – 2 × 10⁻⁵");
  });

  it("is not reported without values", () => {
    expect(formatRange(null, null, 2)).toBe(NOT_REPORTED);
  });
});

describe("formatReported", () => {
  it("does not round what a source reported", () => {
    expect(formatReported(12345)).toBe("12345");
    expect(formatReported(8760)).toBe("8760");
    expect(formatReported(0.123456789)).toBe("0.123457");
  });

  it("is not reported without a value", () => {
    expect(formatReported(null)).toBe(NOT_REPORTED);
  });
});
