import { useCallback, useEffect, useState } from "react";

import { DEFAULT_LANGUAGE, LANGUAGES } from "../constants/languages";

const STORAGE_KEY = "voiceclone.defaultLanguage";

function readStored(): string {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    // Ignore a stored value that's no longer an offered language.
    if (stored && LANGUAGES.some((l) => l.code === stored)) return stored;
  } catch {
    // localStorage unavailable (private mode, etc.) — fall back to the default.
  }
  return DEFAULT_LANGUAGE;
}

// The language preselected when creating a profile. A user preference, stored
// client-side (this is a single-user desktop app), settable from Settings.
export function useDefaultLanguage(): [string, (code: string) => void] {
  const [language, setLanguage] = useState<string>(readStored);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, language);
    } catch {
      // Best-effort persistence; the in-memory value still applies this session.
    }
  }, [language]);

  const update = useCallback((code: string) => setLanguage(code), []);
  return [language, update];
}
