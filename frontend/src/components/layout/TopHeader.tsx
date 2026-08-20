interface TopHeaderProps {
  sidebarOpen: boolean
  onToggleSidebar: () => void
  title: string
}

export function TopHeader({
  sidebarOpen,
  onToggleSidebar,
  title,
}: TopHeaderProps) {
  return (
    <header className="fixed right-0 top-0 z-30 flex h-14 items-center gap-4 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]/80 px-4 backdrop-blur-xl transition-all duration-300 md:left-[260px] left-0">
      <button
        onClick={onToggleSidebar}
        className="rounded-lg p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)] md:hidden"
        aria-label="Toggle sidebar"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d={sidebarOpen ? 'M6 18L18 6M6 6l12 12' : 'M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5'} />
        </svg>
      </button>

      <div className="flex items-center gap-2.5 flex-1 min-w-0">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--primary-subtle)] md:hidden">
          <svg className="h-4 w-4 text-[var(--accent)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        <h1 key={title} className="truncate text-sm font-semibold text-[var(--text-primary)] md:text-base animate-fade_in">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-full border border-[var(--border-color)] bg-[var(--bg-elevated)] px-3 py-1">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--success)] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--success)]"></span>
          </span>
          <span className="text-xs font-medium text-[var(--text-secondary)]">Connected</span>
        </div>
      </div>
    </header>
  )
}
