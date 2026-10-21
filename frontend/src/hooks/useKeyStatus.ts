import { useCallback, useEffect, useState } from "react";

import { clearKey, getKeysStatus, saveKey } from "../services/apiClient";
import type { KeyName, KeysStatusResponse } from "../types/workspace";

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Try again.";
}

/** Which keys are stored (never a key), with save and clear actions for each. */
export function useKeyStatus() {
  const [statuses, setStatuses] = useState<KeysStatusResponse | null>(null);
  const [busy, setBusy] = useState<KeyName | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (name: KeyName, action: () => Promise<unknown>) => {
    setBusy(name);
    setError(null);
    try {
      await action();
      setStatuses(await getKeysStatus());
      return true;
    } catch (failure) {
      setError(message(failure));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  useEffect(() => {
    let live = true;
    getKeysStatus()
      .then((value) => {
        if (live) setStatuses(value);
      })
      .catch((failure: unknown) => {
        if (live) setError(message(failure));
      });
    return () => {
      live = false;
    };
  }, []);

  const save = useCallback((name: KeyName, key: string) => run(name, () => saveKey(name, key)), [run]);
  const clear = useCallback((name: KeyName) => run(name, () => clearKey(name)), [run]);
  return { statuses, busy, error, save, clear };
}
