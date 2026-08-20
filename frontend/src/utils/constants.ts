import type { AppSettings } from '@/types/settings'

export const STORAGE_KEYS = {
  MESSAGES: 'candidate_validation_messages',
  SESSION_ID: 'candidate_validation_session_id',
  SETTINGS: 'candidate_validation_settings',
  REPORTS: 'candidate_validation_reports',
} as const

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'dark',
  autoScroll: true,
  animations: true,
  fontSize: 'medium',
}

export const AUTH = {
  bearerToken: import.meta.env.VITE_BEARER_TOKEN || '',
  apiKey: import.meta.env.VITE_API_KEY || '',
  appId: import.meta.env.VITE_APP_ID || '',
  username: import.meta.env.VITE_USERNAME || '',
} as const

export const NAV_ITEMS = [
  { label: 'Chat', path: '/', icon: 'MessageSquare' },
  { label: 'Reports', path: '/reports', icon: 'FileText' },
  { label: 'Settings', path: '/settings', icon: 'Settings' },
  { label: 'About', path: '/about', icon: 'Info' },
] as const

export const FONT_SIZE_MAP = {
  small: '0.875rem',
  medium: '1rem',
  large: '1.125rem',
} as const

export const ACCEPTED_FILE_TYPES = '.pdf'
export const MAX_FILE_SIZE = 10 * 1024 * 1024

export const EXECUTOR_URL = import.meta.env.VITE_EXECUTOR_URL || ''
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export interface ParsedReport {
  candidate_id: string
  overall_score: number
  recommendation: string
  report_url?: string
  report_url_expiry?: string
  validation_status?: string
  executive_summary?: string
  blob_id?: string
  generated_time: string
}
