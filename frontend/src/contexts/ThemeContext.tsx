import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import type { ThemeMode } from '@/types/settings'
import { themeService } from '@/services/theme.service'

interface ThemeContextValue {
  theme: ThemeMode
  setTheme: (theme: ThemeMode) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({
  children,
  initialTheme = 'dark',
}: {
  children: ReactNode
  initialTheme?: ThemeMode
}) {
  const [theme, setThemeState] = useState<ThemeMode>(initialTheme)

  const applyTheme = useCallback((newTheme: ThemeMode) => {
    themeService.applyTheme(newTheme)
  }, [])

  const setTheme = useCallback(
    (newTheme: ThemeMode) => {
      setThemeState(newTheme)
      applyTheme(newTheme)
    },
    [applyTheme]
  )

  useEffect(() => {
    applyTheme(theme)
  }, [theme, applyTheme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
