import type { AuthPayload, UserSession } from '../state'
import { ApiError, createAuthHeaders, createJsonHeaders, requestJson } from './http'

const SESSION_KEY = 'chillazi.session'

interface BackendUser {
  email: string
  id: number
  name: string
  role?: string | null
  role_name?: string | null
}

interface BackendLoginResponse {
  access_token: string
  token_type: string
  user: BackendUser
}

interface BackendUserResponse {
  email: string
  id: number
  name: string
  role_id: number
  role_name?: string | null
}

function formatName(rawName: string): string {
  return rawName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1).toLowerCase()}`)
    .join(' ')
}

function normalizeSession(user: BackendUser, accessToken: string, chatSessionId: number | null): UserSession {
  return {
    accessToken,
    chatSessionId,
    email: user.email.trim().toLowerCase(),
    id: user.id,
    name: user.name.trim(),
    role: user.role ?? user.role_name ?? null,
  }
}

function isStoredSession(value: unknown): value is UserSession {
  if (!value || typeof value !== 'object') {
    return false
  }

  const candidate = value as Partial<UserSession>

  return (
    typeof candidate.accessToken === 'string' &&
    candidate.accessToken.length > 0 &&
    (candidate.chatSessionId === null || typeof candidate.chatSessionId === 'number') &&
    typeof candidate.email === 'string' &&
    candidate.email.length > 0 &&
    typeof candidate.id === 'number' &&
    Number.isFinite(candidate.id) &&
    typeof candidate.name === 'string' &&
    candidate.name.length > 0 &&
    (candidate.role === null || typeof candidate.role === 'string')
  )
}

function storeSession(session: UserSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

function normalizeApiError(error: unknown, fallbackMessage: string): Error {
  if (!(error instanceof ApiError)) {
    return error instanceof Error ? error : new Error(fallbackMessage)
  }

  if (error.status === 401) {
    return new Error('Invalid email or password.')
  }

  if (
    error.status >= 500 &&
    /unique|duplicate|already exists/i.test(error.message)
  ) {
    return new Error('An account with that email already exists.')
  }

  return new Error(error.message || fallbackMessage)
}

export function persistSession(session: UserSession): void {
  storeSession(session)
}

export function getStoredSession(): UserSession | null {
  try {
    const rawSession = localStorage.getItem(SESSION_KEY)

    if (!rawSession) {
      return null
    }

    const parsedSession = JSON.parse(rawSession) as unknown

    if (!isStoredSession(parsedSession)) {
      return null
    }

    return {
      ...parsedSession,
      email: parsedSession.email.toLowerCase(),
      name: parsedSession.name.trim(),
      role: parsedSession.role ?? null,
    }
  } catch {
    return null
  }
}

export function clearStoredSession(): void {
  localStorage.removeItem(SESSION_KEY)
}

export async function fetchCurrentUser(session = getStoredSession()): Promise<UserSession> {
  if (!session) {
    throw new Error('No active session found.')
  }

  const user = await requestJson<BackendUserResponse>('/api/users/me', {
    headers: createAuthHeaders(session.accessToken),
    method: 'GET',
  })

  const nextSession = normalizeSession(
    {
      email: user.email,
      id: user.id,
      name: user.name,
      role_name: user.role_name ?? null,
    },
    session.accessToken,
    session.chatSessionId,
  )

  storeSession(nextSession)
  return nextSession
}

export async function loginUser(payload: AuthPayload): Promise<UserSession> {
  const email = payload.email.trim().toLowerCase()
  const password = payload.password.trim()

  if (!email || !password) {
    throw new Error('Enter both your email and password to continue.')
  }

  try {
    const response = await requestJson<BackendLoginResponse>(
      "/api/users/login",
      {
        body: JSON.stringify({ email, password }),
        headers: createJsonHeaders(),
        method: "POST",
      },
    );

    const session = normalizeSession(response.user, response.access_token, null)
    storeSession(session)
    return session
  } catch (error) {
    throw normalizeApiError(error, 'Unable to sign in right now.')
  }
}

export async function registerUser(payload: AuthPayload): Promise<UserSession> {
  const fullName = formatName(payload.fullName?.trim() ?? '')
  const email = payload.email.trim().toLowerCase()
  const password = payload.password.trim()

  if (!fullName || !email || !password) {
    throw new Error('Full name, email, and password are required to register.')
  }

  try {
    await requestJson<BackendUserResponse>('/api/users/', {
      body: JSON.stringify({
        email,
        name: fullName,
        password,
      }),
      headers: createJsonHeaders(),
      method: 'POST',
    })

    return await loginUser({ email, password })
  } catch (error) {
    throw normalizeApiError(error, 'Unable to create your account right now.')
  }
}
