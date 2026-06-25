import { createContext, useContext, useEffect, useMemo, useRef, type ReactNode } from "react";
import { applyTheme, pickRandomTheme, type Theme } from "@/lib/themes";

interface ThemeContextValue {
  theme: Theme;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Pick once per session — useRef ensures no re-pick on re-render
  const theme = useRef(pickRandomTheme()).current;

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const value = useMemo(() => ({ theme }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within <ThemeProvider>");
  return ctx;
}
