export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export type ExecutorEventType = 'sessionId' | 'status' | 'complete' | 'error'

export interface ExecutorEvent {
  type: ExecutorEventType
  sessionId?: string
  agent?: string
  status?: string
  result?: string
  error?: string
}

export interface ExecutorOptions {
  onEvent: (event: ExecutorEvent) => void
  onDone: () => void
  onError: (error: string) => void
  signal?: AbortSignal
}

export interface ExecutorConfig {
  bearerToken: string
  apiKey: string
  appId: string
  username: string
}

export interface ExecutorRequestBody {
  userInput: string
  UserInputType: string
  sessionId: string
  executionId: string
  connectionID: string
  isStreaming: boolean
  Username: string
}
