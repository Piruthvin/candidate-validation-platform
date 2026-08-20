import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useRef,
  type ReactNode,
} from 'react'
import type { Message, ExecutorConfig } from '@/types/chat'
import type { UploadedResume } from '@/types/resume'
import type { ParsedReport } from '@/utils/constants'
import { ExecutorService } from '@/services/executor.service'
import { ResumeService } from '@/services/resume.service'
import { storageService } from '@/services/storage.service'
import { AUTH, EXECUTOR_URL, STORAGE_KEYS } from '@/utils/constants'
import { generateId } from '@/utils/formatters'

const resumeService = new ResumeService()

interface ChatState {
  messages: Message[]
  sessionId: string | null
  isLoading: boolean
  isTyping: boolean
  typingText: string
  error: string | null
  uploadedResume: UploadedResume | null
  extractingText: boolean
  showCandidateIdDialog: boolean
  extractedText: string
}

type ChatAction =
  | { type: 'ADD_MESSAGE'; message: Message }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_TYPING'; typing: boolean; text?: string }
  | { type: 'SET_SESSION_ID'; sessionId: string }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'SET_UPLOADED_RESUME'; resume: UploadedResume | null }
  | { type: 'SET_EXTRACTING_TEXT'; extracting: boolean }
  | { type: 'SHOW_CANDIDATE_ID_DIALOG'; show: boolean; extractedText?: string }
  | { type: 'SET_EXTRACTED_TEXT'; text: string }
  | { type: 'CLEAR_CHAT' }

const initialState: ChatState = {
  messages: storageService.get<Message[]>(STORAGE_KEYS.MESSAGES, []),
  sessionId: storageService.get<string | null>(STORAGE_KEYS.SESSION_ID, null),
  isLoading: false,
  isTyping: false,
  typingText: '',
  error: null,
  uploadedResume: null,
  extractingText: false,
  showCandidateIdDialog: false,
  extractedText: '',
}

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.message] }
    case 'SET_LOADING':
      return { ...state, isLoading: action.loading }
    case 'SET_TYPING':
      return {
        ...state,
        isTyping: action.typing,
        typingText: action.text ?? state.typingText,
        error: null,
      }
    case 'SET_SESSION_ID':
      return { ...state, sessionId: action.sessionId }
    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
        isLoading: false,
        isTyping: false,
        extractingText: false,
      }
    case 'SET_UPLOADED_RESUME':
      return { ...state, uploadedResume: action.resume }
    case 'SET_EXTRACTING_TEXT':
      return { ...state, extractingText: action.extracting }
    case 'SHOW_CANDIDATE_ID_DIALOG':
      return {
        ...state,
        showCandidateIdDialog: action.show,
        extractedText: action.extractedText ?? state.extractedText,
      }
    case 'SET_EXTRACTED_TEXT':
      return { ...state, extractedText: action.text }
    case 'CLEAR_CHAT':
      return { ...initialState, messages: [] }
    default:
      return state
  }
}

interface ChatContextValue {
  state: ChatState
  sendMessage: (text: string) => void
  handleResumeUpload: (file: File) => Promise<void>
  submitCandidateId: (candidateId: string) => void
  cancelCandidateId: () => void
  retry: () => void
  clearChat: () => void
  setUploadedResume: (resume: UploadedResume | null) => void
  hasPendingResume: boolean
}

const ChatContext = createContext<ChatContextValue | null>(null)

function formatResult(raw: string | Record<string, unknown>): { content: string; report: ParsedReport | null } {
  let data: Record<string, unknown>

  if (typeof raw === 'string') {
    try {
      data = JSON.parse(raw)
    } catch {
      return { content: raw, report: null }
    }
  } else {
    data = raw
  }

  const candidateId = (data.candidate_id ?? data.candidateId ?? '') as string
  const overallScore = data.overall_score ?? data.overallScore ?? 0
  const recommendation = (data.recommendation ?? '') as string
  const reportUrl = (data.report_url ?? data.reportUrl ?? '') as string
  const blobId = (data.blob_id ?? data.blobId ?? '') as string
  const executiveSummary = (data.executive_summary ?? data.executiveSummary ?? data.summary ?? '') as string
  const validationStatus = (data.validation_status ?? data.validationStatus ?? '') as string

  if (!candidateId) {
    return { content: typeof raw === 'string' ? raw : JSON.stringify(raw), report: null }
  }

  const parsedScore = typeof overallScore === 'number' ? overallScore : parseInt(String(overallScore), 10) || 0

  const report: ParsedReport = {
    candidate_id: candidateId,
    overall_score: parsedScore,
    recommendation,
    report_url: reportUrl,
    blob_id: blobId,
    validation_status: validationStatus,
    executive_summary: executiveSummary,
    generated_time: new Date().toISOString(),
  }

  const scoreEmoji = parsedScore >= 80 ? '🟢' : parsedScore >= 60 ? '🟡' : '🔴'
  const lines: string[] = []

  lines.push('✅ **Candidate validation completed successfully.**')
  lines.push('')
  lines.push(`**Candidate ID:** \`${candidateId}\``)
  lines.push(`**Overall Score:** ${scoreEmoji} ${parsedScore}/100`)
  lines.push(`**Recommendation:** **${recommendation}**`)

  if (executiveSummary) {
    lines.push('')
    lines.push('**Executive Summary**')
    lines.push('')
    lines.push(executiveSummary)
  }

  if (reportUrl) {
    lines.push('')
    lines.push('📄 Report generated successfully.')
    lines.push(`[Open Report](${reportUrl})`)
  }

  return { content: lines.join('\n'), report }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  const executorRef = useRef<ExecutorService | null>(null)
  const lastTextRef = useRef<string>('')
  const sessionIdRef = useRef(state.sessionId)
  sessionIdRef.current = state.sessionId
  const messagesRef = useRef(state.messages)
  messagesRef.current = state.messages

  const persistMessages = useCallback((messages: Message[]) => {
    storageService.set(STORAGE_KEYS.MESSAGES, messages)
  }, [])

  const getExecutor = useCallback(() => {
    if (!executorRef.current) {
      const config: ExecutorConfig = {
        bearerToken: AUTH.bearerToken,
        apiKey: AUTH.apiKey,
        appId: AUTH.appId,
        username: AUTH.username,
      }
      executorRef.current = new ExecutorService(config)
    }
    return executorRef.current
  }, [])

  const executeChat = useCallback(
    async (text: string) => {
      const executor = getExecutor()

      dispatch({ type: 'SET_LOADING', loading: true })
      dispatch({ type: 'SET_TYPING', typing: true, text: 'Thinking...' })

      await executor.execute(
        EXECUTOR_URL,
        text,
        sessionIdRef.current ?? '',
        {
          onEvent: (event) => {
            switch (event.type) {
              case 'sessionId':
                dispatch({ type: 'SET_SESSION_ID', sessionId: event.sessionId! })
                storageService.set(STORAGE_KEYS.SESSION_ID, event.sessionId)
                break
              case 'status':
                dispatch({
                  type: 'SET_TYPING',
                  typing: true,
                  text: event.status ?? 'Processing...',
                })
                break
              case 'complete':
                dispatch({ type: 'SET_TYPING', typing: false })
                dispatch({ type: 'SET_LOADING', loading: false })
                if (event.result) {
                  const { content, report } = formatResult(event.result)
                  const assistantMsg: Message = {
                    id: generateId(),
                    role: 'assistant',
                    content,
                    timestamp: Date.now(),
                  }
                  dispatch({ type: 'ADD_MESSAGE', message: assistantMsg })
                  persistMessages([...messagesRef.current, assistantMsg])
                  if (report) {
                    const existing = storageService.get<ParsedReport[]>(STORAGE_KEYS.REPORTS, [])
                    // Avoid duplicates by candidate_id + blob_id
                    const isDuplicate = existing.some(
                      (r) => r.candidate_id === report.candidate_id && r.blob_id === report.blob_id
                    )
                    if (!isDuplicate) {
                      existing.push(report)
                      storageService.set(STORAGE_KEYS.REPORTS, existing)
                      window.dispatchEvent(new Event('reports-updated'))
                    }
                  }
                }
                break
              case 'error':
                dispatch({ type: 'SET_ERROR', error: event.error ?? 'An error occurred' })
                break
            }
          },
          onDone: () => {
            dispatch({ type: 'SET_LOADING', loading: false })
            dispatch({ type: 'SET_TYPING', typing: false })
          },
          onError: (error) => {
            dispatch({ type: 'SET_ERROR', error })
          },
        }
      )
    },
    [getExecutor, persistMessages]
  )

  const sendMessage = useCallback(
    (text: string) => {
      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
      }

      dispatch({ type: 'ADD_MESSAGE', message: userMsg })
      persistMessages([...messagesRef.current, userMsg])
      lastTextRef.current = text
      executeChat(text)
    },
    [executeChat, persistMessages]
  )

  const handleResumeUpload = useCallback(
    async (file: File) => {
      const error = resumeService.validateFile(file)
      if (error) {
        dispatch({ type: 'SET_ERROR', error })
        return
      }

      dispatch({ type: 'SET_EXTRACTING_TEXT', extracting: true })

      try {
        const { rawText } = await resumeService.extractFromPdf(file)

        dispatch({ type: 'SET_EXTRACTING_TEXT', extracting: false })
        dispatch({ type: 'SHOW_CANDIDATE_ID_DIALOG', show: true, extractedText: rawText })
        dispatch({
          type: 'SET_UPLOADED_RESUME',
          resume: {
            file,
            rawText,
            candidateId: '',
            fileName: file.name,
            fileSize: file.size,
          },
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to extract resume text'
        dispatch({ type: 'SET_ERROR', error: message })
        dispatch({ type: 'SET_EXTRACTING_TEXT', extracting: false })
      }
    },
    []
  )

  const submitCandidateId = useCallback(
    (candidateId: string) => {
      dispatch({ type: 'SHOW_CANDIDATE_ID_DIALOG', show: false })

      const payload = JSON.stringify({
        candidate_id: candidateId,
        raw_resume_text: state.extractedText,
      })

      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: `Resume: ${state.uploadedResume?.fileName ?? 'uploaded'} (ID: ${candidateId})`,
        timestamp: Date.now(),
      }

      dispatch({ type: 'ADD_MESSAGE', message: userMsg })
      persistMessages([...messagesRef.current, userMsg])
      lastTextRef.current = payload
      dispatch({ type: 'SET_UPLOADED_RESUME', resume: null })
      executeChat(payload)
    },
    [state.extractedText, state.uploadedResume, executeChat, persistMessages]
  )

  const cancelCandidateId = useCallback(() => {
    dispatch({ type: 'SHOW_CANDIDATE_ID_DIALOG', show: false })
    dispatch({ type: 'SET_UPLOADED_RESUME', resume: null })
    dispatch({ type: 'SET_EXTRACTED_TEXT', text: '' })
  }, [])

  const retry = useCallback(() => {
    const lastText = lastTextRef.current
    if (lastText) {
      executeChat(lastText)
    }
  }, [executeChat])

  const clearChat = useCallback(() => {
    const executor = getExecutor()
    executor.cancel()
    dispatch({ type: 'CLEAR_CHAT' })
    dispatch({ type: 'SET_UPLOADED_RESUME', resume: null })
    storageService.clear(
      STORAGE_KEYS.MESSAGES,
      STORAGE_KEYS.SESSION_ID
    )
  }, [getExecutor])

  const setUploadedResume = useCallback(
    (resume: UploadedResume | null) => {
      dispatch({ type: 'SET_UPLOADED_RESUME', resume })
    },
    []
  )

  const hasPendingResume = state.uploadedResume !== null

  return (
    <ChatContext.Provider
      value={{
        state,
        sendMessage,
        handleResumeUpload,
        submitCandidateId,
        cancelCandidateId,
        retry,
        clearChat,
        setUploadedResume,
        hasPendingResume,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
