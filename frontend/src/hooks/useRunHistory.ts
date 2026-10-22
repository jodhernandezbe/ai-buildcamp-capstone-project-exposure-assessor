import { useCallback, useState } from "react";

import type { RailRun } from "../components/layout/LeftNavRail";

/**
 * This page session's runs, newest first. Held in memory only: the conversations themselves
 * live on the server, and nothing here is written to browser storage.
 */
export function useRunHistory(firstId: string) {
  const [runs, setRuns] = useState<RailRun[]>([{ id: firstId, title: null }]);

  const add = useCallback(
    (id: string) => setRuns((now) => (now.some((run) => run.id === id) ? now : [{ id, title: null }, ...now])),
    [],
  );
  /** Title a run by its first message; later messages leave the title alone. */
  const title = useCallback(
    (id: string, text: string) =>
      setRuns((now) => now.map((run) => (run.id === id && run.title === null ? { ...run, title: text } : run))),
    [],
  );
  const remove = useCallback((id: string) => setRuns((now) => now.filter((run) => run.id !== id)), []);
  return { runs, add, title, remove };
}
