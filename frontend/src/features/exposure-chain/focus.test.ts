import { describe, expect, it } from "vitest";

import { facility } from "../../test/fixtures";
import { resolveFocus } from "./focus";

const a = facility({ frs_id: "A" });
const b = facility({ frs_id: "B" });

describe("resolveFocus", () => {
  it("follows the chat's selection when nothing is pinned", () => {
    expect(resolveFocus([a, b], "B", null)).toBe(b);
  });

  it("shows the pin over the chat's selection", () => {
    expect(resolveFocus([a, b], "A", "B")).toBe(b);
  });

  it("falls back to the selection when the pinned facility is gone", () => {
    expect(resolveFocus([a], "A", "B")).toBe(a);
  });

  it("is null when nothing matches", () => {
    expect(resolveFocus([], null, null)).toBeNull();
    expect(resolveFocus([a], "X", "Y")).toBeNull();
  });
});
