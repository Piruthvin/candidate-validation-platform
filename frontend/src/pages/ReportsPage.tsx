import { useReports } from '@/contexts/ReportContext'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { formatDate } from '@/utils/formatters'
import type { ParsedReport } from '@/utils/constants'

function scoreColor(score: number): 'success' | 'warning' | 'danger' {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function LocalReportCard({
  report,
  onOpen,
  onDelete,
  index,
}: {
  report: ParsedReport
  onOpen: (url: string) => void
  onDelete: (candidateId: string, blobId?: string) => void
  index: number
}) {
  const color = scoreColor(report.overall_score)
  const delay = Math.min(index * 100, 500)
  
  return (
    <div 
      className="group flex flex-col rounded-2xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-[var(--primary-subtle)] animate-slide_up opacity-0 [animation-fill-mode:forwards]"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="truncate text-lg font-semibold text-[var(--text-primary)]">
            Candidate {report.candidate_id}
          </h3>
          <p className="mt-1 text-xs text-[var(--text-muted)] font-mono">
            ID: {report.candidate_id}
          </p>
        </div>
        <div className={`flex shrink-0 items-center justify-center h-12 w-12 rounded-full border-2 border-[var(--${color})] bg-[var(--${color})]/10 text-[var(--${color})] font-bold animate-pulse_glow`}>
          {report.overall_score}
        </div>
      </div>

      <div className="mt-5 flex gap-3">
        <div className="flex-1 rounded-xl bg-[var(--bg-primary)] px-4 py-3 border border-[var(--border-color)]">
          <p className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Overall</p>
          <p className="mt-1 text-sm font-bold text-[var(--text-primary)]">
            {report.overall_score}%
          </p>
        </div>
        <div className="flex-1 rounded-xl bg-[var(--bg-primary)] px-4 py-3 border border-[var(--border-color)]">
          <p className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Recommendation</p>
          <p className={`mt-1 text-sm font-bold ${
            report.recommendation.toUpperCase() === 'HIRE' || report.recommendation.toUpperCase() === 'STRONG HIRE' 
              ? 'text-[var(--success)]' 
              : report.recommendation.toUpperCase() === 'REJECT' 
                ? 'text-[var(--danger)]' 
                : 'text-[var(--warning)]'
          }`}>
            {report.recommendation}
          </p>
        </div>
      </div>

      {report.executive_summary && (
        <p className="mt-5 line-clamp-3 text-sm leading-relaxed text-[var(--text-secondary)] flex-1">
          {report.executive_summary}
        </p>
      )}

      <div className="mt-6 flex items-center justify-between pt-4 border-t border-[var(--border-color)]">
        <span className="text-xs font-medium text-[var(--text-muted)]">
          {formatDate(report.generated_time)}
        </span>
        <div className="flex items-center gap-2">
          {report.report_url && (
            <button
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--primary)] to-[var(--primary-hover)] px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[var(--primary-subtle)]"
              onClick={() => onOpen(report.report_url!)}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              Open
            </button>
          )}
          <button
            className="rounded-xl p-2 text-[var(--text-muted)] transition-colors hover:bg-red-500/10 hover:text-red-500"
            onClick={() => onDelete(report.candidate_id, report.blob_id)}
            title="Delete Report"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export function ReportsPage() {
  const { reports, deleteReport } = useReports()

  return (
    <ErrorBoundary>
      <div className="flex h-full flex-col">
        <div className="border-b border-[var(--border-color)] px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">Validation Reports</h2>
              <p className="mt-1 text-sm text-[var(--text-secondary)]">
                {reports.length} report{reports.length !== 1 ? 's' : ''} generated
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-[var(--bg-primary)]">
          {reports.length === 0 ? (
            <div className="flex h-full min-h-[60vh] items-center justify-center animate-fade_in">
              <div className="flex max-w-md flex-col items-center gap-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-10 text-center shadow-2xl shadow-[var(--bg-secondary)]">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--primary-subtle)]">
                  <svg className="h-10 w-10 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">No validation reports yet.</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                    Upload a resume to generate your first validation report.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {reports.map((r, idx) => (
                <LocalReportCard
                  key={`${r.candidate_id}-${r.blob_id}-${idx}`}
                  report={r}
                  index={idx}
                  onOpen={(url) => window.open(url, '_blank')}
                  onDelete={deleteReport}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}
