import { useCallback, useRef, useState, type DragEvent } from 'react'
import { cn } from '@/utils/cn'
import { formatFileSize } from '@/utils/formatters'

interface UploadZoneProps {
  onUpload: (file: File) => void
  uploadedFile: { fileName: string; fileSize: number } | null
  onRemove: () => void
  disabled: boolean
  extracting: boolean
}

export function UploadZone({
  onUpload,
  uploadedFile,
  onRemove,
  disabled,
  extracting,
}: UploadZoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) onUpload(file)
    },
    [onUpload]
  )

  const handleBrowse = useCallback(() => {
    inputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) onUpload(file)
      if (inputRef.current) inputRef.current.value = ''
    },
    [onUpload]
  )

  if (uploadedFile) {
    return (
      <div className="flex items-center gap-3 border-t border-[var(--border-color)] bg-[var(--primary-subtle)] px-4 py-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-subtle)]">
          <svg className="h-4 w-4 text-[var(--accent)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate text-sm text-[var(--text-primary)]">{uploadedFile.fileName}</p>
          <p className="text-xs text-[var(--text-muted)]">{formatFileSize(uploadedFile.fileSize)}</p>
        </div>
        <button
          onClick={onRemove}
          disabled={disabled}
          className="rounded-lg p-1.5 text-[var(--text-muted)] transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-50"
          title="Remove file"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'flex cursor-pointer items-center gap-3 border-t border-[var(--border-color)] px-4 py-3 transition-colors',
        dragging ? 'bg-[var(--primary-subtle)]' : 'hover:bg-[var(--bg-elevated)]/50',
        (disabled || extracting) && 'pointer-events-none opacity-50'
      )}
      onClick={handleBrowse}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-color)] bg-[var(--bg-elevated)]">
        {extracting ? (
          <svg className="h-4 w-4 animate-spin text-[var(--accent)]" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="h-4 w-4 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        )}
      </div>
      <p className="text-sm text-[var(--text-muted)]">
        {extracting ? (
          'Extracting text from PDF...'
        ) : (
          <>
            <span className="font-medium text-[var(--text-secondary)]">Upload resume</span>
            {' '}or drag and drop PDF
          </>
        )}
      </p>
    </div>
  )
}
