import type { ThemeMode } from '@/types/settings'

export class ThemeService {
  applyTheme(theme: ThemeMode): void {
    document.documentElement.setAttribute('data-theme', theme)

    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
}

export const themeService = new ThemeService()
