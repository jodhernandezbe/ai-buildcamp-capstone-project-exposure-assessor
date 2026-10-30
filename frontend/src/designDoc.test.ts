import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

// Keeps DESIGN.md truthful: every token declared in the light theme block of index.css is
// documented in its "## Tokens" section, and every documented token is declared.
const CSS_PATH = "src/index.css";
const DOC_PATH = "DESIGN.md";

/** Tokens declared in the first `:root { ... }` block (the light theme). */
function declaredTokens(css: string): Set<string> {
  const start = css.indexOf(":root");
  const open = css.indexOf("{", start);
  const close = css.indexOf("}", open);
  if (start < 0 || open < 0 || close < 0) return new Set();
  const block = css.slice(open + 1, close);
  return new Set([...block.matchAll(/^\s*--([\w-]+)\s*:/gm)].map((m) => m[1] ?? ""));
}

/** Tokens written as `--name` inside the "## Tokens" section of the design document. */
function documentedTokens(markdown: string): Set<string> {
  const heading = markdown.search(/^## Tokens\s*$/m);
  if (heading < 0) return new Set();
  const rest = markdown.slice(heading + 1);
  const next = rest.search(/^## /m);
  const section = next < 0 ? rest : rest.slice(0, next);
  return new Set([...section.matchAll(/`--([\w-]+)`/g)].map((m) => m[1] ?? ""));
}

/** Tokens present on one side only. */
function tokenDrift(css: string, markdown: string): { undocumented: string[]; stale: string[] } {
  const declared = declaredTokens(css);
  const documented = documentedTokens(markdown);
  return {
    undocumented: [...declared].filter((t) => !documented.has(t)).sort(),
    stale: [...documented].filter((t) => !declared.has(t)).sort(),
  };
}

const CSS_FIXTURE = ":root {\n  --bg: #fff;\n  --fg: #000;\n}\n.x { --other: 1; }\n";
const DOC_FIXTURE = "# Design\n\n## Tokens\n\n| `--bg` | | |\n| `--fg` | | |\n\n## Copy\n\n`--not-a-token`\n";

describe("design document tokens", () => {
  it("reads only the light theme block and only the Tokens section", () => {
    expect([...declaredTokens(CSS_FIXTURE)]).toEqual(["bg", "fg"]);
    expect([...documentedTokens(DOC_FIXTURE)]).toEqual(["bg", "fg"]);
  });

  it("names a declared token that is not documented", () => {
    const css = CSS_FIXTURE.replace("--fg: #000;", "--fg: #000;\n  --accent: #06c;");
    expect(tokenDrift(css, DOC_FIXTURE)).toEqual({ undocumented: ["accent"], stale: [] });
  });

  it("names a documented token that is no longer declared", () => {
    const css = CSS_FIXTURE.replace("  --fg: #000;\n", "");
    expect(tokenDrift(css, DOC_FIXTURE)).toEqual({ undocumented: [], stale: ["fg"] });
  });

  it("reports nothing when a stylesheet has no :root block or a document has no Tokens section", () => {
    expect(declaredTokens(".x { --a: 1; }").size).toBe(0);
    expect(documentedTokens("# Design\n\n## Copy\n`--a`").size).toBe(0);
  });

  it("matches the real stylesheet and DESIGN.md", () => {
    const css = readFileSync(CSS_PATH, "utf8");
    const doc = readFileSync(DOC_PATH, "utf8");
    expect(declaredTokens(css).size).toBeGreaterThan(0);
    expect(tokenDrift(css, doc)).toEqual({ undocumented: [], stale: [] });
  });
});
