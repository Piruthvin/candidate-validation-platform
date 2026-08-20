export type ThemeMode = 'dark' | 'light'
export type FontSizeOption = 'small' | 'medium' | 'large'

export interface AppSettings {
  theme: ThemeMode
  autoScroll: boolean
  animations: boolean
  fontSize: FontSizeOption
}
