export class StorageService {
  get<T>(key: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return fallback
      const parsed = JSON.parse(raw) as T
      
      // Type safety fallback check
      if (Array.isArray(fallback) && !Array.isArray(parsed)) {
        return fallback
      }
      if (typeof fallback === 'object' && fallback !== null && (typeof parsed !== 'object' || parsed === null)) {
        return fallback
      }
      
      return parsed
    } catch {
      return fallback
    }
  }

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // storage full or unavailable
    }
  }

  remove(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch {
      // unavailable
    }
  }

  clear(...keys: string[]): void {
    for (const key of keys) {
      this.remove(key)
    }
  }
}

export const storageService = new StorageService()
