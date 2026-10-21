import { readFileSync } from "node:fs";

const css = readFileSync("src/index.css", "utf8");

// WCAG 2.x relative luminance and contrast ratio for the design tokens (text needs 4.5:1).
const AA_TEXT = 4.5;
const DARK_AT = css.indexOf("@media (prefers-color-scheme: dark)");

type Theme = Map<string, string>;

function tokens(block: string): Theme {
  return new Map([...block.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\b/g)].map((m) => [m[1] ?? "", m[2] ?? ""]));
}

function channel(hex: string, start: number): number {
  const c = parseInt(hex.slice(start, start + 2), 16) / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

const luminance = (hex: string): number =>
  0.2126 * channel(hex, 1) + 0.7152 * channel(hex, 3) + 0.0722 * channel(hex, 5);

function contrast(a: string, b: string): number {
  const lighter = Math.max(luminance(a), luminance(b));
  const darker = Math.min(luminance(a), luminance(b));
  return (lighter + 0.05) / (darker + 0.05);
}

const light = tokens(css.slice(0, DARK_AT));
const dark: Theme = new Map([...light, ...tokens(css.slice(DARK_AT, css.indexOf("@theme")))]);

const PAIRS: [string, string][] = [
  ["fg", "bg"],
  ["fg", "surface-solid"],
  ["fg-2", "bg"],
  ["fg-2", "surface-solid"],
  ["accent", "bg"],
  ["accent", "surface-solid"],
  ["accent-fg", "accent"],
  ["ok", "surface-solid"],
  ["warn", "surface-solid"],
  ["bad", "surface-solid"],
  ["ok", "bg"],
  ["warn", "bg"],
  ["bad", "bg"],
];

describe.each([
  ["light", light],
  ["dark", dark],
])("%s theme text contrast", (_, theme) => {
  it.each(PAIRS)("%s on %s meets WCAG AA", (fg, bg) => {
    expect(contrast(theme.get(fg) ?? "#000000", theme.get(bg) ?? "#000000")).toBeGreaterThanOrEqual(AA_TEXT);
  });
});
