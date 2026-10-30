import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { facility, workspace } from "../../test/fixtures";
import { useFocusedFacility } from "./useFocusedFacility";

const a = facility({ frs_id: "A" });
const b = facility({ frs_id: "B" });
const base = workspace({ facilities: [a, b], selected_frs_id: "A" });

describe("useFocusedFacility", () => {
  it("starts on the chat's selection and follows a map pin", () => {
    const { result } = renderHook(() => useFocusedFacility(base, 0));
    expect(result.current.facility?.frs_id).toBe("A");
    act(() => result.current.onPin("B"));
    expect(result.current.facility?.frs_id).toBe("B");
  });

  it("drops the pin when the chat selects another facility", () => {
    const { result, rerender } = renderHook(({ ws }) => useFocusedFacility(ws, 0), { initialProps: { ws: base } });
    act(() => result.current.onPin("B"));
    rerender({ ws: { ...base, selected_frs_id: "B" } });
    expect(result.current.facility?.frs_id).toBe("B");
    rerender({ ws: { ...base, selected_frs_id: "A" } });
    expect(result.current.facility?.frs_id).toBe("A");
  });

  it("drops the pin when the workspace is replaced", () => {
    const { result, rerender } = renderHook(({ epoch }) => useFocusedFacility(base, epoch), { initialProps: { epoch: 0 } });
    act(() => result.current.onPin("B"));
    rerender({ epoch: 1 });
    expect(result.current.facility?.frs_id).toBe("A");
  });
});
