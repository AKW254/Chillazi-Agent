import type { UserSession } from '../state'
import { createAuthHeaders, requestJson } from './http'

interface StreamChatMessageOptions {
  message: string
  onChunk: (content: string) => void
  onSessionId?: (sessionId: number) => void
  session: UserSession
  signal?: AbortSignal
}

interface BackendChatResponse {
  response: string
  session_id: number
}

function createAbortError(): Error {
  return new DOMException('The request was aborted.', 'AbortError')
}

function throwIfAborted(signal?: AbortSignal): void {
  if (!signal?.aborted) {
    return
  }

  throw signal.reason instanceof Error ? signal.reason : createAbortError()
}

function pause(durationMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      signal?.removeEventListener('abort', handleAbort)
      resolve()
    }, durationMs)

    const handleAbort = () => {
      window.clearTimeout(timeoutId)
      signal?.removeEventListener('abort', handleAbort)
      reject(createAbortError())
    }

    if (signal) {
      signal.addEventListener('abort', handleAbort, { once: true })
    }
  })
}

function splitIntoChunks(content: string): string[] {
  return content.match(/\S+\s*/g) ?? [content]
}

function getChunkDelay(chunk: string): number {
  const normalizedChunk = chunk.trim()

  if (!normalizedChunk) {
    return 30
  }

  if (/[.!?]$/.test(normalizedChunk)) {
    return 140
  }

  if (normalizedChunk.length <= 3) {
    return 55
  }

  return Math.min(110, 40 + normalizedChunk.length * 6)
}

export async function streamChatMessage({
  message,
  onChunk,
  onSessionId,
  session,
  signal,
}: StreamChatMessageOptions): Promise<string> {
  const trimmedMessage = message.trim()

  if (!trimmedMessage) {
    throw new Error('A message is required.')
  }

  throwIfAborted(signal)

  const payload: {
    message: string
    session_id?: number
  } = {
    message: trimmedMessage,
  }

  if (typeof session.chatSessionId === 'number') {
    payload.session_id = session.chatSessionId
  }

  const response = await requestJson<BackendChatResponse>('/api/chat', {
    body: JSON.stringify(payload),
    headers: createAuthHeaders(session.accessToken),
    method: 'POST',
    signal,
  })

  if (typeof response.session_id === 'number') {
    onSessionId?.(response.session_id)
  }

  const reply =
    typeof response.response === 'string' && response.response.trim()
      ? response.response
      : 'The assistant returned an empty response.'
  const chunks = splitIntoChunks(reply)
  let streamedReply = ''

  for (const chunk of chunks) {
    throwIfAborted(signal)
    await pause(getChunkDelay(chunk), signal)
    streamedReply += chunk
    onChunk(streamedReply)
  }

  return streamedReply
}
