export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(status: number, message: string, payload: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function getApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

  if (configuredBaseUrl) {
    return configuredBaseUrl.replace(/\/+$/, '')
  }

  // Default to same-origin requests so local Vite proxying can handle `/api`
  // during development without tripping CORS.
  return ''
}

function buildApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path
  }

  const baseUrl = getApiBaseUrl()
  return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

function extractErrorMessage(payload: unknown, fallbackMessage: string): string {
  if (typeof payload === 'string' && payload.trim()) {
    return payload
  }

  if (!payload || typeof payload !== 'object') {
    return fallbackMessage
  }

  const candidate = payload as {
    detail?: unknown
    message?: unknown
  }

  if (typeof candidate.detail === 'string' && candidate.detail.trim()) {
    return candidate.detail
  }

  if (Array.isArray(candidate.detail) && candidate.detail.length > 0) {
    return candidate.detail
      .map((entry) =>
        typeof entry === 'string'
          ? entry
          : entry && typeof entry === 'object' && 'msg' in entry && typeof entry.msg === 'string'
            ? entry.msg
            : JSON.stringify(entry),
      )
      .join(', ')
  }

  if (typeof candidate.message === 'string' && candidate.message.trim()) {
    return candidate.message
  }

  return fallbackMessage
}

export function createJsonHeaders(headers?: HeadersInit): Headers {
  const normalizedHeaders = new Headers(headers)

  if (!normalizedHeaders.has('Content-Type')) {
    normalizedHeaders.set('Content-Type', 'application/json')
  }

  return normalizedHeaders
}

export function createAuthHeaders(token: string, headers?: HeadersInit): Headers {
  const normalizedHeaders = createJsonHeaders(headers)
  normalizedHeaders.set('Authorization', `Bearer ${token}`)
  return normalizedHeaders
}

export async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response

  try {
    response = await fetch(buildApiUrl(path), init)
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw error
    }

    const baseUrl = getApiBaseUrl()
    const targetDescription = baseUrl || '/api'

    throw new Error(
      `Could not reach the backend API at ${targetDescription}. Check that the backend is running and that the local API proxy/CORS setup is correct.`,
    )
  }

  const rawBody = await response.text()
  let payload: unknown = null

  if (rawBody) {
    try {
      payload = JSON.parse(rawBody)
    } catch {
      payload = rawBody
    }
  }

  if (!response.ok) {
    throw new ApiError(
      response.status,
      extractErrorMessage(payload, `Request failed with status ${response.status}.`),
      payload,
    )
  }

  return payload as T
}
