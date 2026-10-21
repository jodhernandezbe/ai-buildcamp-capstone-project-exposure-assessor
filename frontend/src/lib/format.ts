/** Shown for a value no tool reported (never zero, never a dash that reads as zero). */
export const NOT_REPORTED = "not reported";

// Magnitudes outside [1e-3, 1e5) are written in scientific notation, like a cancer risk.
const SMALLEST_PLAIN = 1e-3;
const LARGEST_PLAIN = 1e5;
const SUPERSCRIPT: Record<string, string> = {
  "-": "⁻",
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
};

const superscript = (exponent: number): string =>
  [...String(exponent)].map((c) => SUPERSCRIPT[c] ?? c).join("");

/** 0.000012 with 2 digits -> "1.2 × 10⁻⁵". */
export function formatScientific(value: number, digits: number): string {
  const [mantissa, exponent] = value.toExponential(Math.max(digits - 1, 0)).split("e");
  return `${Number(mantissa)} × 10${superscript(Number(exponent))}`;
}

/** The value with `digits` significant digits, without trailing zeros: 0.8200 -> "0.82". */
export function formatSignificant(value: number, digits: number): string {
  return String(Number(value.toPrecision(digits)));
}

/** A metric: scientific notation when very small or large, else significant digits. */
export function formatNumber(value: number | null | undefined, digits: number): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NOT_REPORTED;
  const magnitude = Math.abs(value);
  if (magnitude !== 0 && (magnitude < SMALLEST_PLAIN || magnitude >= LARGEST_PLAIN)) {
    return formatScientific(value, digits);
  }
  return formatSignificant(value, digits);
}

/** A quantity exactly as a source reported it (a release in pounds, hours per year), not rounded. */
export function formatReported(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NOT_REPORTED;
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 6, useGrouping: false }).format(value);
}

/** A metric with its unit; an absent value has no unit. */
export function formatWithUnit(
  value: number | null | undefined,
  unit: string,
  digits: number,
): string {
  const text = formatNumber(value, digits);
  return text === NOT_REPORTED ? text : `${text} ${unit}`;
}

/** A whole count with thousands separators; absent -> "not reported". */
export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NOT_REPORTED;
  return new Intl.NumberFormat("en-US").format(value);
}

/** Text a tool reported, or "not reported". */
export const orNotReported = (value: string | null | undefined): string =>
  value && value.trim() ? value : NOT_REPORTED;

/** A range over stacks: one value when both ends are the same, else "low – high". */
export function formatRange(
  low: number | null | undefined,
  high: number | null | undefined,
  digits: number,
): string {
  const first = formatNumber(low, digits);
  const last = formatNumber(high, digits);
  return first === last ? first : `${first} – ${last}`;
}
