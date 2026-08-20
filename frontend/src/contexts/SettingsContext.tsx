import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import type { AppSettings } from '@/types/settings'
import { storageService } from '@/services/storage.service'
import { DEFAULT_SETTINGS, STORAGE_KEYS, FONT_SIZE_MAP } from '@/utils/constants'
import { useTheme } from './ThemeContext'

interface SettingsContextValue {
  settings: AppSettings
  updateSettings: (partial: Partial<AppSettings>) => void
  resetSettings: () => void
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(() => {
    const stored = storageService.get<Partial<AppSettings>>(STORAGE_KEYS.SETTINGS, {})
    return { ...DEFAULT_SETTINGS, ...stored }
  })
  const { setTheme } = useTheme()

  useEffect(() => {
    storageService.set(STORAGE_KEYS.SETTINGS, settings)
  }, [settings])

  useEffect(() => {
    setTheme(settings.theme)
    document.documentElement.style.fontSize = FONT_SIZE_MAP[settings.fontSize]
  }, [settings.theme, settings.fontSize, setTheme])

  const updateSettings = useCallback((partial: Partial<AppSettings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...partial }
      return next
    })
  }, [])

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS)
  }, [])

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}
