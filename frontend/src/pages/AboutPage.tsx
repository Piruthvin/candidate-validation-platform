import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

export function AboutPage() {
  return (
    <ErrorBoundary>
      <div className="mx-auto h-full max-w-4xl overflow-y-auto px-6 py-10 animate-fade_in">
        <div className="flex flex-col items-center mb-12 text-center animate-slide_up opacity-0 [animation-fill-mode:forwards]">
          <div className="flex h-20 w-20 items-center justify-center rounded-[1.5rem] bg-gradient-to-br from-[var(--primary)] to-[var(--primary-hover)] shadow-xl shadow-[var(--primary-subtle)]">
            <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-[var(--text-primary)]">
            Candidate Validation Platform
          </h1>
        </div>

        <div className="space-y-8">
          <div className="rounded-3xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-8 shadow-sm animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:100ms]">
            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-4">Description</h3>
            <p className="text-base leading-relaxed text-[var(--text-secondary)]">
              Candidate Validation Platform is an AI-powered recruiter assistant designed to streamline candidate validation through intelligent resume analysis, structured validation workflows, and automated report generation.
            </p>
            <p className="text-base leading-relaxed text-[var(--text-secondary)] mt-4">
              The platform enables recruiters to:
            </p>
            <ul className="mt-4 space-y-2 text-base text-[var(--text-secondary)] list-disc pl-5">
              <li>Analyze resumes</li>
              <li>Validate candidate information</li>
              <li>Review generated validation reports</li>
              <li>Track candidate assessments</li>
              <li>Improve hiring decisions</li>
            </ul>
          </div>

          <div className="rounded-3xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-8 shadow-sm animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:200ms]">
            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-6">Workflow</h3>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-center">
              <div className="flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-[var(--primary-subtle)] text-[var(--primary)] flex items-center justify-center mb-3">1</div>
                <span className="text-sm font-medium text-[var(--text-primary)]">Resume Upload</span>
              </div>
              <svg className="hidden md:block h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
              <svg className="md:hidden h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3" />
              </svg>

              <div className="flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-[var(--primary-subtle)] text-[var(--primary)] flex items-center justify-center mb-3">2</div>
                <span className="text-sm font-medium text-[var(--text-primary)]">Resume Text Extraction</span>
              </div>
              <svg className="hidden md:block h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
              <svg className="md:hidden h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3" />
              </svg>

              <div className="flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-[var(--primary-subtle)] text-[var(--primary)] flex items-center justify-center mb-3">3</div>
                <span className="text-sm font-medium text-[var(--text-primary)]">Candidate Validation</span>
              </div>
              <svg className="hidden md:block h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
              <svg className="md:hidden h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3" />
              </svg>

              <div className="flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-[var(--primary-subtle)] text-[var(--primary)] flex items-center justify-center mb-3">4</div>
                <span className="text-sm font-medium text-[var(--text-primary)]">Report Generation</span>
              </div>
              <svg className="hidden md:block h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
              <svg className="md:hidden h-6 w-6 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3" />
              </svg>

              <div className="flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-[var(--primary-subtle)] text-[var(--primary)] flex items-center justify-center mb-3">5</div>
                <span className="text-sm font-medium text-[var(--text-primary)]">Recruiter Review</span>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-8 shadow-sm animate-slide_up opacity-0 [animation-fill-mode:forwards] [animation-delay:300ms]">
            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-4">Mission</h3>
            <p className="text-base leading-relaxed text-[var(--text-secondary)]">
              Deliver faster, more reliable, and more consistent candidate validation while reducing manual verification effort.
            </p>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}
