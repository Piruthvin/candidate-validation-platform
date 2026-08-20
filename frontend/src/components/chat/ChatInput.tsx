import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react'
import { cn } from '@/utils/cn'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled,
  placeholder = 'Type a message...',
}: ChatInputProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [text, adjustHeight])

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }, [text, disabled, onSend])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  return (
    <div className="border-t border-[var(--border-color)] bg-[var(--bg-secondary)]/80 px-4 py-3 backdrop-blur-xl">
      <div className="mx-auto flex max-w-4xl items-end gap-2">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            className={cn(
              'w-full resize-none rounded-xl border bg-[var(--bg-elevated)] px-4 py-3 pr-12 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none transition-all',
              'border-[var(--border-color)] focus:border-[var(--primary)]/40 focus:ring-1 focus:ring-[var(--primary)]/20',
              'disabled:cursor-not-allowed disabled:opacity-50'
            )}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-all',
            text.trim() && !disabled
              ? 'bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]'
              : 'bg-[var(--bg-elevated)] text-[var(--text-muted)] cursor-not-allowed border border-[var(--border-color)]'
          )}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>
    </div>
  )
}
