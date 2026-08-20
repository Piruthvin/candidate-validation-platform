import { useState, useCallback, useEffect, type KeyboardEvent } from 'react'
import { cn } from '@/utils/cn'

interface CandidateIdDialogProps {
  open: boolean
  fileName: string
  onSubmit: (candidateId: string) => void
  onCancel: () => void
}

export function CandidateIdDialog({
  open,
  fileName,
  onSubmit,
  onCancel,
}: CandidateIdDialogProps) {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed) {
      setError('Candidate ID is required')
      return
    }
    setError('')
    onSubmit(trimmed)
    setValue('')
  }, [value, onSubmit])

  const handleCancel = useCallback(() => {
    setValue('')
    setError('')
    onCancel()
  }, [onCancel])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleCancel()
    }
    document.addEventListener('keydown', handler as unknown as EventListener)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler as unknown as EventListener)
      document.body.style.overflow = ''
    }
  }, [open, handleCancel])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleCancel} />
      <div className="relative w-full max-w-md animate-scale-in rounded-2xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-6 shadow-2xl">
        <div className="mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--primary-subtle)]">
            <svg className="h-5 w-5 text-[var(--accent)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
        </div>

        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Enter Candidate ID
        </h2>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          Resume extracted from: <span className="font-medium text-[var(--text-primary)]">{fileName}</span>
        </p>

        <div className="mt-4">
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
            Candidate ID
          </label>
          <input
            type="text"
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              if (error) setError('')
            }}
            onKeyDown={handleKeyDown}
            placeholder="e.g. ZR_10001"
            autoFocus
            className={cn(
              'w-full rounded-xl border bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none transition-colors',
              error
                ? 'border-red-500/50 focus:border-red-500/50 focus:ring-1 focus:ring-red-500/20'
                : 'border-[var(--border-color)] focus:border-[var(--primary)]/40 focus:ring-1 focus:ring-[var(--primary)]/20'
            )}
          />
          {error && (
            <p className="mt-1.5 text-xs text-red-400">{error}</p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={handleCancel}
            className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="rounded-xl bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  )
}
