export function EmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center px-4 animate-fade_in">
      <div className="flex max-w-3xl flex-col items-center gap-10 text-center">
        <div className="flex h-24 w-24 items-center justify-center rounded-[2rem] bg-gradient-to-br from-[var(--primary)] to-[var(--primary-hover)] shadow-2xl shadow-[var(--primary-subtle)] animate-scale_in">
          <svg className="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        
        <div className="space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Candidate Validation Platform
          </h2>
          <p className="mx-auto max-w-lg text-base leading-relaxed text-[var(--text-secondary)]">
            AI-powered recruiter assistant for validating candidates, analyzing resumes and generating comprehensive validation reports.
          </p>
        </div>

        <div className="grid w-full grid-cols-1 gap-5 sm:grid-cols-3">
          <div className="glass rounded-2xl p-6 text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-[var(--primary-subtle)] animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:150ms]">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary-subtle)]">
              <svg className="h-6 w-6 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <h3 className="font-semibold text-[var(--text-primary)]">✓ Resume Analysis</h3>
          </div>
          
          <div className="glass rounded-2xl p-6 text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-[var(--primary-subtle)] animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:300ms]">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary-subtle)]">
              <svg className="h-6 w-6 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-[var(--text-primary)]">✓ Candidate Validation</h3>
          </div>
          
          <div className="glass rounded-2xl p-6 text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-[var(--primary-subtle)] animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:450ms]">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary-subtle)]">
              <svg className="h-6 w-6 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h3 className="font-semibold text-[var(--text-primary)]">✓ Report Generation</h3>
          </div>
        </div>
      </div>
    </div>
  )
}
