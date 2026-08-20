import type {
  ExecutorEvent,
  ExecutorOptions,
  ExecutorConfig,
  ExecutorRequestBody,
} from '@/types/chat'

export class ExecutorService {
  private abortController: AbortController | null = null

  constructor(private config: ExecutorConfig) {}

  cancel(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
  }

  async execute(
    endpointUrl: string,
    userInput: string,
    sessionId: string,
    options?: ExecutorOptions
  ): Promise<void> {
    if (!endpointUrl || endpointUrl === 'undefined') {
      options?.onError?.('Executor URL is not configured. Check VITE_EXECUTOR_URL in .env')
      return
    }
    this.abortController = new AbortController()
    const signal = options?.signal ?? this.abortController.signal

    const body: ExecutorRequestBody = {
      userInput,
      UserInputType: '',
      sessionId: sessionId || '',
      executionId: '',
      connectionID: '',
      isStreaming: true,
      Username: this.config.username,
    }

    try {
      const response = await fetch(endpointUrl, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.config.bearerToken}`,
          'x-api-key': this.config.apiKey,
          'x-app-id': this.config.appId,
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(body),
        signal,
      })

      if (!response.ok) {
        options?.onError?.('The validation service is currently unavailable. Please try again later.')
        return
      }

      const contentType = response.headers.get('content-type') ?? ''

      if (contentType.includes('event-stream')) {
        await this.handleStream(response, options)
      } else {
        const text = await response.text()
        this.handleNonStream(text, options)
      }

      options?.onDone?.()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }
      options?.onError?.('Failed to connect to the validation service. Please check your connection and try again.')
    } finally {
      this.abortController = null
    }
  }

  private async handleStream(
    response: Response,
    options?: ExecutorOptions
  ): Promise<void> {
    const reader = response.body?.getReader()
    if (!reader) {
      options?.onError?.('Response body is not readable')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let readCount = 0

    try {
      while (true) {
        const { done, value } = await reader.read()
        readCount++

        if (value) {
          const decoded = decoder.decode(value, { stream: true })
          buffer += decoded
        }

        const chunks = buffer.split('\n\n')

        buffer = chunks.pop() ?? ''

        for (const chunk of chunks) {
          this.parseSSEChunk(chunk, options)
        }

        if (done) {
          break
        }
      }

      if (buffer.trim()) {
        this.parseSSEChunk(buffer, options)
      }
    } finally {
      reader.releaseLock()
    }
  }

  private handleNonStream(
    text: string,
    options?: ExecutorOptions
  ): void {
    const chunks = text.split('\n\n')
    for (const chunk of chunks) {
      this.parseSSEChunk(chunk, options)
    }
  }

  private parseSSEChunk(chunk: string, options?: ExecutorOptions): void {
    const lines = chunk.split('\n')
    let jsonStr = ''
    let inData = false
    for (const line of lines) {
      if (line.startsWith('data:')) {
        inData = true
        const rest = line.slice(5).trim()
        if (rest) {
          jsonStr = rest
        }
      } else if (inData) {
        jsonStr += line
      }
    }
    if (!jsonStr) return
    try {
      const parsed = JSON.parse(jsonStr)
      const event = this.parseEvent(parsed)
      if (event) {
        options?.onEvent?.(event)
      }
    } catch (e) {
      // Ignore malformed chunks in production
    }
  }

  private parseEvent(data: Record<string, unknown>): ExecutorEvent | null {
    const type = (data.Type ?? data.type) as string | undefined

    if (type === 'status' || type === 'Status') {
      const status = (data.Status ?? data.status ?? data.Agent ?? '') as string
      return { type: 'status', status }
    }

    if (type === 'complete' || type === 'Complete') {
      const result = (data.Result ?? '') as string
      return { type: 'complete', result }
    }

    const sessionId = data.SessionId as string | undefined
    if (sessionId) {
      return { type: 'sessionId', sessionId }
    }

    return null
  }
}
