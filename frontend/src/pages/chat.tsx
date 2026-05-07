import { useEffect, useRef, useState, type FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage, UserSession } from '../state'

interface ChatPageProps {
  adminHref?: string
  landingHref: string
  messages: ChatMessage[]
  onLogout: () => void
  onSendMessage: (message: string) => Promise<void>
  pending: boolean
  session: UserSession
  streamingMessageId: string | null
}

const quickPrompts = [
  'Show me menu?',
  'What is Chillazi?',
  'How do I use this?',
]

export function ChatPage({
  adminHref,
  landingHref,
  messages,
  onLogout,
  onSendMessage,
  pending,
  session,
  streamingMessageId,
}: ChatPageProps) {
  const [draft, setDraft] = useState('')
  const messagesRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const container = messagesRef.current

    if (!container) {
      return
    }

    container.scrollTop = container.scrollHeight
  }, [messages, streamingMessageId])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const nextMessage = draft.trim()

    if (!nextMessage) {
      return
    }

    setDraft('')
    await onSendMessage(nextMessage)
  }

  //Clear think tag from from llm response
  function cleanMessageContent(content: string) {
    return content.replace(/Thinking\.\.\./g, '').trim()
  }

  return (
    <main className="mx-auto grid min-h-screen w-full max-w-8xl items-center px-4 py-5 ">
      <section className="grid animate-[fade-up_0.7s_ease_both] gap-4 lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="grid content-start gap-4 rounded-[1.55rem] border border-[rgba(116,78,51,0.14)] bg-[rgba(255,248,240,0.84)] p-5 shadow-[0_28px_80px_rgba(98,49,16,0.14)] backdrop-blur-[18px]">
          <a
            className="inline-flex items-center gap-2 font-semibold text-clay-700"
            href={landingHref}
          >
            <span>{"<"}</span>
            <span>Back to landing</span>
          </a>

          <div>
            <p className="m-0 text-xs font-bold tracking-[0.16em] text-clay-700 uppercase">
              Signed in
            </p>
            <h1 className="mt-2 font-display text-5xl leading-none tracking-[-0.04em] text-espresso-900">
              {session.name}
            </h1>
            <p className="mt-2 text-[rgba(107,92,80,1)]">{session.email}</p>
          </div>

          <div className="rounded-[1.5rem] border border-[rgba(203,95,49,0.12)] bg-linear-to-br from-[rgba(255,255,255,0.86)] to-[rgba(255,243,233,0.72)] p-5">
            <strong className="block text-espresso-900">Quick prompts</strong>
            <div className="mt-3 grid gap-3">
              {quickPrompts.map((prompt) => (
                <button
                  className="rounded-2xl border border-[rgba(203,95,49,0.14)] bg-[rgba(255,255,255,0.6)] px-4 py-3 text-left text-sm text-espresso-900 transition duration-200 hover:-translate-y-0.5"
                  key={prompt}
                  onClick={() => setDraft(prompt)}
                  type="button"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {adminHref ? (
            <a
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] bg-[rgba(255,255,255,0.65)] px-5 py-3 text-sm font-semibold text-espresso-900 transition duration-200 hover:-translate-y-0.5"
              href={adminHref}
            >
              Open Admin Dashboard
            </a>
          ) : null}

          <button
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] bg-[rgba(255,255,255,0.45)] px-5 py-3 text-sm font-medium text-espresso-900 transition duration-200 hover:-translate-y-0.5"
            onClick={onLogout}
            type="button"
          >
            Logout
          </button>
        </aside>

        <section className="grid min-h-[80vh] gap-4 rounded-[1.55rem] border border-[rgba(116,78,51,0.1)] bg-[rgba(255,251,247,0.78)] p-5 shadow-[0_28px_80px_rgba(98,49,16,0.14)] backdrop-blur-[18px]">
          <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="m-0 text-xs font-bold tracking-[0.16em] text-clay-700 uppercase">
                Conversation
              </p>
              <h2 className="mt-1 text-[1.1rem] font-semibold text-espresso-900">
                Chillazi Assistant
              </h2>
            </div>
            <span className="inline-flex rounded-full bg-[rgba(255,232,220,0.8)] px-3.5 py-2 text-sm font-bold text-clay-700">
              {pending && streamingMessageId
                ? "Assistant is streaming"
                : pending
                  ? "Assistant is thinking"
                  : "Ready"}
            </span>
          </header>

          <div
            ref={messagesRef}
            className="grid max-h-[56vh] content-start gap-3 overflow-auto pr-1 lg:max-h-none"
            aria-busy={pending}
            aria-live="polite"
          >
            {messages.map((message) => (
              <article
                className={
                  message.role === "user" ? "flex justify-end" : "flex"
                }
                key={message.id}
              >
                <div
                  className={
                    message.role === "user"
                      ? "max-w-full rounded-[1.25rem] bg-linear-to-br from-clay-500 to-clay-700 px-4 py-4 text-sand-50 sm:max-w-[42rem]"
                      : "max-w-full rounded-[1.25rem] border border-[rgba(116,78,51,0.12)] bg-[rgba(255,255,255,0.82)] px-4 py-4 text-espresso-900 sm:max-w-[42rem]"
                  }
                >
                  <span
                    className={
                      message.role === "user"
                        ? "mb-2 inline-flex text-xs font-bold tracking-[0.08em] text-[rgba(255,245,236,0.82)] uppercase"
                        : "mb-2 inline-flex text-xs font-bold tracking-[0.08em] text-clay-700 uppercase"
                    }
                  >
                    {message.role === "user" ? "You" : "Chillazi"}
                  </span>
                  <p className="m-0 whitespace-pre-wrap">
                    <ReactMarkdown>
                      {cleanMessageContent(message.content) ||
                        (message.id === streamingMessageId
                          ? "Thinking..."
                          : "")}
                    </ReactMarkdown>

                    {message.id === streamingMessageId && (
                      <span
                        aria-hidden="true"
                        className="ml-1 inline-block animate-pulse text-clay-500"
                      >
                        |
                      </span>
                    )}
                  </p>
                </div>
              </article>
            ))}
          </div>

          <form className="mt-auto grid gap-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="sr-only">Type your message</span>
              <textarea
                className="min-h-28 w-full resize-y rounded-2xl border border-[rgba(116,78,51,0.14)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-espresso-900 outline-none transition focus:border-[rgba(203,95,49,0.6)] focus:shadow-[0_0_0_4px_rgba(203,95,49,0.12)]"
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask about menu or others..."
                rows={3}
                value={draft}
              />
            </label>

            <button
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-5 py-3 text-sm font-semibold text-sand-50 shadow-[0_14px_28px_rgba(157,63,25,0.22)] transition duration-200 hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-70 disabled:hover:translate-y-0"
              disabled={pending || !draft.trim()}
              type="submit"
            >
              Send message
            </button>
          </form>
        </section>
      </section>
    </main>
  );
}
