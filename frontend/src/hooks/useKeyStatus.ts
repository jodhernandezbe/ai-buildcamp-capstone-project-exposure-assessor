import { useCallback, useEffect, useState } from "react";

import { clearKey, getKeysStatus, saveKey } from "../services/apiClient";
import type { KeyName, KeysStatusResponse } from "../types/workspace";

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Try again.";
}

/** How the last save or clear of one key went; its text never holds any part of a key. */
export interface KeyOutcome {
  kind: "success" | "error";
  message: string;
}

export type KeyOutcomes = Partial<Record<KeyName, KeyOutcome>>;

/** Which keys are stored (never a key), with save and clear actions and each key's last outcome. */
export function useKeyStatus() {
  const [statuses, setStatuses] = useState<KeysStatusResponse | null>(null);
  const [busy, setBusy] = useState<KeyName | null>(null);
  const [outcomes, setOutcomes] = useState<KeyOutcomes>({});
  const [loadError, setLoadError] = useState<string | null>(null);

  const run = useCallback(async (name: KeyName, done: string, action: () => Promise<unknown>) => {
    setBusy(name);
    setOutcomes((now) => ({ ...now, [name]: undefined }));
    try {
      await action();
      setStatuses(await getKeysStatus());
      setOutcomes((now) => ({ ...now, [name]: { kind: "success", message: done } }));
      return true;
    } catch (failure) {
      setOutcomes((now) => ({ ...now, [name]: { kind: "error", message: message(failure) } }));
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
        if (live) setLoadError(message(failure));
      });
    return () => {
      live = false;
    };
  }, []);

  const save = useCallback(
    (name: KeyName, key: string) => run(name, "Key saved.", () => saveKey(name, key)),
    [run],
  );
  const clear = useCallback((name: KeyName) => run(name, "Key cleared.", () => clearKey(name)), [run]);
  return { statuses, busy, outcomes, loadError, save, clear };
}
