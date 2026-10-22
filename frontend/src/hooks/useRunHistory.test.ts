import { act, renderHook } from "@testing-library/react";

import { useRunHistory } from "./useRunHistory";

describe("useRunHistory", () => {
  it("starts with the first run, untitled", () => {
    const { result } = renderHook(() => useRunHistory("a"));
    expect(result.current.runs).toEqual([{ id: "a", title: null }]);
  });

  it("lists new runs first and ignores a run it already has", () => {
    const { result } = renderHook(() => useRunHistory("a"));
    act(() => result.current.add("b"));
    act(() => result.current.add("b"));
    expect(result.current.runs.map((run) => run.id)).toEqual(["b", "a"]);
  });

  it("titles a run by its first message only", () => {
    const { result } = renderHook(() => useRunHistory("a"));
    act(() => result.current.title("a", "map hexane"));
    act(() => result.current.title("a", "and benzene"));
    expect(result.current.runs[0]?.title).toBe("map hexane");
  });

  it("removes a run and never touches browser storage", () => {
    localStorage.clear();
    sessionStorage.clear();
    const { result } = renderHook(() => useRunHistory("a"));
    act(() => result.current.add("b"));
    act(() => result.current.remove("a"));
    expect(result.current.runs.map((run) => run.id)).toEqual(["b"]);
    expect(localStorage.length + sessionStorage.length).toBe(0);
  });
});
