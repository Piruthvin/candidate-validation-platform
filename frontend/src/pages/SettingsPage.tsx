import { useSettings } from '@/contexts/SettingsContext'
import { useChat } from '@/contexts/ChatContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { cn } from '@/utils/cn'

export function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useSettings()
  const { clearChat } = useChat()

  return (
    <ErrorBoundary>
      <div className="mx-auto h-full max-w-3xl overflow-y-auto px-6 py-6">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">Settings</h2>
        <p className="mt-0.5 text-sm text-[var(--text-secondary)]">
          Customize your experience
        </p>

        <div className="mt-6 space-y-6">
          <Card className="divide-y divide-[var(--border-color)]">
            <Section title="Theme">
              <div className="flex gap-2">
                {(
                  [
                    { value: 'dark' as const, label: 'Dark', icon: 'moon' },
                    { value: 'light' as const, label: 'Light', icon: 'sun' },
                  ]
                ).map((option) => (
                  <button
                    key={option.value}
                    onClick={() => updateSettings({ theme: option.value })}
                    className={cn(
                      'flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm transition-all',
                      settings.theme === option.value
                        ? 'border-[var(--primary)]/50 bg-[var(--primary-subtle)] text-[var(--accent)]'
                        : 'border-[var(--border-color)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:border-[var(--border-color)] hover:text-[var(--text-primary)]'
                    )}
                  >
                    {option.icon === 'moon' ? (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                      </svg>
                    )}
                    {option.label}
                  </button>
                ))}
              </div>
            </Section>

            <Section title="Font Size">
              <div className="flex gap-2">
                {(
                  [
                    { value: 'small' as const, label: 'Small' },
                    { value: 'medium' as const, label: 'Medium' },
                    { value: 'large' as const, label: 'Large' },
                  ]
                ).map((option) => (
                  <button
                    key={option.value}
                    onClick={() => updateSettings({ fontSize: option.value })}
                    className={cn(
                      'rounded-xl border px-4 py-2.5 text-sm transition-all',
                      settings.fontSize === option.value
                        ? 'border-[var(--primary)]/50 bg-[var(--primary-subtle)] text-[var(--accent)]'
                        : 'border-[var(--border-color)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:border-[var(--border-color)] hover:text-[var(--text-primary)]'
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </Section>

            <Section title="Preferences">
              <div className="space-y-3">
                {(
                  [
                    {
                      key: 'autoScroll' as const,
                      label: 'Auto Scroll',
                      desc: 'Automatically scroll to new messages',
                    },
                    {
                      key: 'animations' as const,
                      label: 'Animations',
                      desc: 'Enable UI animations and transitions',
                    },
                  ]
                ).map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center justify-between rounded-lg px-1 py-2"
                  >
                    <div>
                      <p className="text-sm text-[var(--text-primary)]">{item.label}</p>
                      <p className="text-xs text-[var(--text-muted)]">{item.desc}</p>
                    </div>
                    <button
                      onClick={() =>
                        updateSettings({ [item.key]: !settings[item.key] })
                      }
                      className={cn(
                        'relative h-6 w-11 rounded-full transition-colors',
                        settings[item.key]
                          ? 'bg-[var(--primary)]'
                          : 'bg-[var(--bg-elevated)] border border-[var(--border-color)]'
                      )}
                    >
                      <span
                        className={cn(
                          'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform',
                          settings[item.key]
                            ? 'translate-x-5'
                            : 'translate-x-0'
                        )}
                      />
                    </button>
                  </label>
                ))}
              </div>
            </Section>
          </Card>

          <Card className="divide-y divide-[var(--border-color)]">
            <Section title="Data">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[var(--text-primary)]">Clear Chat History</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      Remove all messages and session data
                    </p>
                  </div>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={clearChat}
                  >
                    Clear
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[var(--text-primary)]">Reset All Settings</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      Restore default settings
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={resetSettings}
                  >
                    Reset
                  </Button>
                </div>
              </div>
            </Section>
          </Card>
        </div>
      </div>
    </ErrorBoundary>
  )
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="px-5 py-4">
      <h3 className="mb-3 text-sm font-medium text-[var(--text-muted)]">{title}</h3>
      {children}
    </div>
  )
}
