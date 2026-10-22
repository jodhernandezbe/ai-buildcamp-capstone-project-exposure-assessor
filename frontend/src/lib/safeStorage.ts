/** The part of `Storage` the layout needs; reads and writes never throw. */
export interface SafeStorage {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
}

/**
 * Browser storage for convenience only (panel sizes, never anything sensitive). It can be empty
 * or throw (private windows, blocked site data), so every access is guarded.
 */
export const safeStorage: SafeStorage = {
  getItem(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      // storage unavailable: sizes simply are not remembered
    }
  },
};
