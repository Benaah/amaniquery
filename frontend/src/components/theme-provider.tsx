"use client"

import * as React from "react"

type Theme = "judicial-suede" | "savanna-tech"
type Mode = "light" | "dark"

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  defaultMode?: Mode
  storageKey?: string
}

type ThemeProviderState = {
  theme: Theme
  mode: Mode
  setTheme: (theme: Theme) => void
  setMode: (mode: Mode) => void
}

const initialState: ThemeProviderState = {
  theme: "judicial-suede",
  mode: "light",
  setTheme: () => null,
  setMode: () => null,
}

const ThemeProviderContext = React.createContext<ThemeProviderState>(initialState)

export function ThemeProvider({
  children,
  defaultTheme = "judicial-suede",
  defaultMode = "light",
  storageKey = "ui-theme",
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = React.useState<Theme>(defaultTheme)
  const [mode, setMode] = React.useState<Mode>(defaultMode)

  React.useEffect(() => {
    const storedTheme = localStorage.getItem(`${storageKey}-theme`) as Theme
    const storedMode = localStorage.getItem(`${storageKey}-mode`) as Mode
    
    if (storedTheme) setTheme(storedTheme)
    if (storedMode) setMode(storedMode)
  }, [storageKey])

  React.useEffect(() => {
    const root = window.document.documentElement

    root.removeAttribute("data-theme")
    root.classList.remove("dark")

    if (theme !== "judicial-suede") {
      root.setAttribute("data-theme", theme)
    }

    if (mode === "dark") {
      root.classList.add("dark")
    }
  }, [theme, mode])

  const value = {
    theme,
    mode,
    setTheme: (theme: Theme) => {
      localStorage.setItem(`${storageKey}-theme`, theme)
      setTheme(theme)
    },
    setMode: (mode: Mode) => {
      localStorage.setItem(`${storageKey}-mode`, mode)
      setMode(mode)
    },
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = React.useContext(ThemeProviderContext)

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider")

  return context
}