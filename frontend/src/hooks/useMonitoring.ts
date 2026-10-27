import { useCallback, useEffect, useRef, useState } from "react";

import { getMonitoringSession, getMonitoringSessions } from "../services/apiClient";
import type { SessionDetailResponse, SessionsResponse } from "../types/workspace";

const LIST_FAILED = "The sessions could not be loaded.";
const DETAIL_FAILED = "The session could not be loaded.";

/** A request in one of its states; a failure keeps only a user-safe message. */
export type Loadable<T> =
  { status: "loading" } | { status: "loaded"; value: T } | { status: "failed"; message: string };

const loading = { status: "loading" } as const;

async function read<T>(request: () => Promise<T>, fallback: string): Promise<Loadable<T>> {
  try {
    return { status: "loaded", value: await request() };
  } catch (error) {
    return {
      status: "failed",
      message: error instanceof Error ? `${fallback} ${error.message}` : fallback,
    };
  }
}

/**
 * The Monitoring view's data: the recorded sessions (read on mount and on `refresh`) and the
 * timeline of the selected one. A reply that arrives after a newer request was made is dropped,
 * so a slow answer never overwrites a fresh one.
 */
export function useMonitoring() {
  const [sessions, setSessions] = useState<Loadable<SessionsResponse>>(loading);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Loadable<SessionDetailResponse>>(loading);
  const latest = useRef({ list: 0, detail: 0 });

  useEffect(() => {
    const mine = ++latest.current.list;
    void read(getMonitoringSessions, LIST_FAILED).then((next) => {
      if (mine === latest.current.list) setSessions(next);
    });
  }, []);

  const refresh = useCallback(async () => {
    const mine = ++latest.current.list;
    setSessions(loading);
    const next = await read(getMonitoringSessions, LIST_FAILED);
    if (mine === latest.current.list) setSessions(next);
  }, []);

  const select = useCallback(async (sessionId: string | null) => {
    const mine = ++latest.current.detail;
    setSelected(sessionId);
    if (sessionId === null) return;
    setDetail(loading);
    const next = await read(() => getMonitoringSession(sessionId), DETAIL_FAILED);
    if (mine === latest.current.detail) setDetail(next);
  }, []);

  return { sessions, selected, detail, refresh, select };
}
