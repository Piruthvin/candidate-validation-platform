interface TypingIndicatorProps {
  text?: string
}

export function TypingIndicator({ text = 'Thinking...' }: TypingIndicatorProps) {
  return (
    <div className="flex gap-3 px-4 py-3 animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:150ms]">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--primary-subtle)]">
        <svg className="h-4 w-4 text-[var(--accent)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      </div>
      <div className="flex max-w-[70%] items-center gap-3 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-elevated)] px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:0ms]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:300ms]" />
        </div>
        <span className="text-sm text-[var(--text-secondary)]">{text}</span>
      </div>
    </div>
  )
}
