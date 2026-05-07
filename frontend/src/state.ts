export type AuthMode = 'login' | 'register'

export interface UserSession {
  accessToken: string
  chatSessionId: number | null
  id: number
  name: string
  email: string
  role: string | null
}

export interface AuthPayload {
  fullName?: string
  email: string
  password: string
}

export interface ChatMessage {
  id: string
  role: 'assistant' | 'user'
  content: string
}

export function createMessageId(prefix: string): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}-${crypto.randomUUID()}`
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function createStarterMessages(name = 'there'): ChatMessage[] {
  const safeName = name.trim() || 'there'

  return [
    {
      id: createMessageId('assistant'),
      role: 'assistant',
      content: `Hi ${safeName}, welcome to Chillazi. What do you wish to order today? You can ask me anything about our menu, and I'll be happy to help!`,
    },
    
  ]
}
