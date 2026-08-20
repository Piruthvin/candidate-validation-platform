import { useCallback } from 'react'
import { useChat } from '@/contexts/ChatContext'
import { ChatBubble } from '@/components/chat/ChatBubble'
import { ChatInput } from '@/components/chat/ChatInput'
import { TypingIndicator } from '@/components/chat/TypingIndicator'
import { EmptyState } from '@/components/chat/EmptyState'
import { UploadZone } from '@/components/chat/UploadZone'
import { CandidateIdDialog } from '@/components/chat/CandidateIdDialog'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { useAutoScroll } from '@/hooks/useAutoScroll'

export function ChatPage() {
  const {
    state,
    sendMessage,
    handleResumeUpload,
    submitCandidateId,
    cancelCandidateId,
    retry,
    clearChat,
  } = useChat()

  const scrollRef = useAutoScroll<HTMLDivElement>([
    state.messages,
    state.isTyping,
  ])

  const handleUpload = useCallback(
    (file: File) => {
      handleResumeUpload(file)
    },
    [handleResumeUpload]
  )

  const handleRemoveFile = useCallback(() => {
    cancelCandidateId()
  }, [cancelCandidateId])

  return (
    <ErrorBoundary>
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-[var(--border-color)] px-4 py-2.5">
          <span className="text-xs font-medium text-[var(--text-muted)]">
            {state.messages.length > 0
              ? `${state.messages.length} messages`
              : 'Start a conversation'}
          </span>
          {state.messages.length > 0 && (
            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              Clear
            </button>
          )}
        </div>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto scroll-smooth"
        >
          <div className="mx-auto max-w-4xl">
            {state.messages.length === 0 && !state.isLoading ? (
              <div className="flex h-full min-h-[calc(100vh-280px)] items-center justify-center">
                <EmptyState />
              </div>
            ) : (
              <div className="py-4">
                {state.messages.map((msg) => (
                  <ChatBubble
                    key={msg.id}
                    message={msg}
                    onRetry={msg.role === 'user' ? retry : undefined}
                  />
                ))}
                {state.isTyping && (
                  <TypingIndicator text={state.typingText} />
                )}
                {state.error && (
                  <div className="mx-4 mt-2 flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
                    <svg className="h-5 w-5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                    <p className="flex-1 text-sm text-red-300">{state.error}</p>
                    <button
                      onClick={retry}
                      className="rounded-lg bg-red-600/10 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-600/20"
                    >
                      Retry
                    </button>
                    <button
                      onClick={() => retry()}
                      className="rounded-lg p-1.5 text-red-400/50 transition-colors hover:text-red-400"
                      title="Dismiss"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <UploadZone
          onUpload={handleUpload}
          uploadedFile={
            state.uploadedResume
              ? {
                  fileName: state.uploadedResume.fileName,
                  fileSize: state.uploadedResume.fileSize,
                }
              : null
          }
          onRemove={handleRemoveFile}
          disabled={state.isLoading}
          extracting={state.extractingText}
        />

        <ChatInput
          onSend={sendMessage}
          disabled={state.isLoading}
          placeholder="Type a message..."
        />

        <CandidateIdDialog
          open={state.showCandidateIdDialog}
          fileName={state.uploadedResume?.fileName ?? ''}
          onSubmit={submitCandidateId}
          onCancel={cancelCandidateId}
        />
      </div>
    </ErrorBoundary>
  )
}
