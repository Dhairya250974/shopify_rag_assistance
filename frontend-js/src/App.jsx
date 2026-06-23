import { useEffect, useMemo, useState } from "react";
import { Home } from "./pages/Home/Home";
import { checkBackendHealth } from "./services/api";

const THEME_KEY = "shopify-rag-theme";

function getInitialTheme() {
  const stored = window.localStorage.getItem(THEME_KEY);
  if (stored === "dark") return true;
  if (stored === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export default function App() {
  const [isDark, setIsDark] = useState(getInitialTheme);
  const [backendDetected, setBackendDetected] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    window.localStorage.setItem(THEME_KEY, isDark ? "dark" : "light");
  }, [isDark]);

  useEffect(() => {
    let active = true;

    checkBackendHealth().then((isHealthy) => {
      if (active) setBackendDetected(isHealthy);
    });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({
      isDark,
      toggleTheme: () => setIsDark((dark) => !dark)
    }),
    [isDark]
  );

  return <Home isDark={value.isDark} backendDetected={backendDetected} onToggleTheme={value.toggleTheme} />;
}
