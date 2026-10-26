import { useCallback, useRef, useState } from "react";

import { saveFile } from "../lib/saveFile";
import { getReport } from "../services/apiClient";

const NOT_GENERATED = "The report could not be generated.";

/** Download the current thread's Word report, one request at a time, keeping its failure. */
export function useReportDownload() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const running = useRef(false);

  const download = useCallback(async (threadId: string) => {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError(null);
    try {
      const file = await getReport(threadId);
      saveFile(file.blob, file.name);
    } catch (failure) {
      setError(failure instanceof Error ? `${NOT_GENERATED} ${failure.message}` : NOT_GENERATED);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }, []);

  const dismiss = useCallback(() => setError(null), []);
  return { busy, error, download, dismiss };
}
