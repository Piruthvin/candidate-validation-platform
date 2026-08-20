import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import type { ParsedReport } from '@/utils/constants'
import { storageService } from '@/services/storage.service'
import { STORAGE_KEYS } from '@/utils/constants'

interface ReportContextValue {
  reports: ParsedReport[]
  deleteReport: (candidateId: string, blobId?: string) => void
}

const ReportContext = createContext<ReportContextValue | null>(null)

export function ReportProvider({ children }: { children: ReactNode }) {
  const [reports, setReports] = useState<ParsedReport[]>([])

  const loadReports = useCallback(() => {
    const stored = storageService.get<ParsedReport[]>(STORAGE_KEYS.REPORTS, [])
    // Sort by latest generated_time
    stored.sort((a, b) => new Date(b.generated_time).getTime() - new Date(a.generated_time).getTime())
    setReports(stored)
  }, [])

  useEffect(() => {
    loadReports()
    window.addEventListener('reports-updated', loadReports)
    return () => window.removeEventListener('reports-updated', loadReports)
  }, [loadReports])

  const deleteReport = useCallback(
    (candidateId: string, blobId?: string) => {
      const stored = storageService.get<ParsedReport[]>(STORAGE_KEYS.REPORTS, [])
      const updated = stored.filter(
        (r) => !(r.candidate_id === candidateId && (!blobId || r.blob_id === blobId))
      )
      storageService.set(STORAGE_KEYS.REPORTS, updated)
      setReports(updated)
    },
    []
  )

  return (
    <ReportContext.Provider
      value={{
        reports,
        deleteReport,
      }}
    >
      {children}
    </ReportContext.Provider>
  )
}

export function useReports(): ReportContextValue {
  const ctx = useContext(ReportContext)
  if (!ctx) throw new Error('useReports must be used within ReportProvider')
  return ctx
}
