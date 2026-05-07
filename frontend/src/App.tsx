import "./app.css";
import { useEffect, useRef, useState } from "react";
import { ChatPage } from "./pages/chat";
import { LandingPage } from "./pages/landing";
import { AboutUsPage } from "./pages/about us";
import { LoginPage } from "./pages/login";
import { AdminPage } from "./pages/admin";
import { buildHref, navigateTo, resolveRoute, type AppRoute } from "./router";
import { streamChatMessage } from "./services/api";
import {
  clearStoredSession,
  fetchCurrentUser,
  getStoredSession,
  loginUser,
  persistSession,
  registerUser,
} from "./services/auth";
import { ApiError } from "./services/http";
import {
  createMessageId,
  createStarterMessages,
  type AuthMode,
  type AuthPayload,
  type ChatMessage,
  type UserSession,
} from "./state";

function getInitialSession(): UserSession | null {
  return getStoredSession();
}

function getInitialRoute(): AppRoute {
  const storedSession = getStoredSession();
  return resolveRoute(
    window.location.hash,
    Boolean(storedSession),
    storedSession?.role === "admin",
  );
}

function getInitialMessages(): ChatMessage[] {
  return createStarterMessages(getStoredSession()?.name);
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function App() {
  const initialSession = getInitialSession();
  const streamControllerRef = useRef<AbortController | null>(null);
  const [session, setSession] = useState<UserSession | null>(initialSession);
  const [route, setRoute] = useState<AppRoute>(getInitialRoute);
  const [messages, setMessages] = useState<ChatMessage[]>(getInitialMessages);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(initialSession === null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null,
  );

  useEffect(() => {
    const syncRoute = () => {
      setRoute(
        resolveRoute(
          window.location.hash,
          Boolean(session),
          session?.role === "admin",
        ),
      );
    };

    syncRoute();
    window.addEventListener("hashchange", syncRoute);

    return () => {
      window.removeEventListener("hashchange", syncRoute);
    };
  }, [session]);

  useEffect(() => {
    return () => {
      streamControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const storedSession = getStoredSession();

    if (!storedSession) {
      setAuthReady(true);
      return;
    }

    let isActive = true;

    fetchCurrentUser(storedSession)
      .then((validatedSession) => {
        if (!isActive) {
          return;
        }

        setSession(validatedSession);
        setMessages(createStarterMessages(validatedSession.name));
      })
      .catch((sessionError) => {
        if (!isActive) {
          return;
        }

        if (sessionError instanceof ApiError && sessionError.status === 401) {
          clearStoredSession();
          setSession(null);
          setMessages(createStarterMessages());
          return;
        }

        setSession(storedSession);
      })
      .finally(() => {
        if (isActive) {
          setAuthReady(true);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const loginHref = buildHref({ name: "login", mode: "login" });
  const registerHref = buildHref({ name: "login", mode: "register" });
  const landingHref = buildHref({ name: "landing" });
  const aboutusHref = buildHref({ name: "about us" });
  const adminHref = buildHref({ name: "admin" });
  const chatHref = buildHref({ name: "chat" });

  const handleModeChange = (mode: AuthMode) => {
    setError(null);
    navigateTo({ name: "login", mode });
  };

  const handleSessionExpired = (message: string) => {
    streamControllerRef.current?.abort();
    streamControllerRef.current = null;
    clearStoredSession();
    setSession(null);
    setMessages(createStarterMessages());
    setPending(false);
    setStreamingMessageId(null);
    setError(message);
    navigateTo({ name: "login", mode: "login" });
  };

  const handleAuthSubmit = async (mode: AuthMode, payload: AuthPayload) => {
    setPending(true);
    setError(null);

    try {
      const nextSession =
        mode === "register"
          ? await registerUser(payload)
          : await loginUser(payload);

      setSession(nextSession);
      setMessages(createStarterMessages(nextSession.name));
      navigateTo(nextSession.role === "admin" ? { name: "admin" } : { name: "chat" });
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "The auth flow hit an unexpected issue.",
      );
    } finally {
      setPending(false);
    }
  };

  const handleLogout = () => {
    streamControllerRef.current?.abort();
    streamControllerRef.current = null;
    clearStoredSession();
    setSession(null);
    setMessages(createStarterMessages());
    setPending(false);
    setStreamingMessageId(null);
    navigateTo({ name: "landing" });
  };

  const handleSendMessage = async (content: string) => {
    if (!session) {
      navigateTo({ name: "login", mode: "login" });
      return;
    }

    const trimmedContent = content.trim();

    if (!trimmedContent || pending) {
      return;
    }

    const assistantMessageId = createMessageId("assistant");
    const controller = new AbortController();

    streamControllerRef.current = controller;
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: createMessageId("user"),
        role: "user",
        content: trimmedContent,
      },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
      },
    ]);
    setPending(true);
    setStreamingMessageId(assistantMessageId);

    try {
      await streamChatMessage({
        message: trimmedContent,
        onChunk: (contentChunk) => {
          setMessages((currentMessages) =>
            currentMessages.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: contentChunk }
                : message,
            ),
          );
        },
        onSessionId: (sessionId) => {
          setSession((currentSession) => {
            if (!currentSession || currentSession.chatSessionId === sessionId) {
              return currentSession;
            }

            const nextSession = {
              ...currentSession,
              chatSessionId: sessionId,
            };

            persistSession(nextSession);
            return nextSession;
          });
        },
        session,
        signal: controller.signal,
      });
    } catch (sendError) {
      if (isAbortError(sendError)) {
        return;
      }

      if (sendError instanceof ApiError && sendError.status === 401) {
        handleSessionExpired("Your session expired. Please sign in again.");
        return;
      }

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content:
                  "The assistant could not respond just now. Try sending the message again.",
              }
            : message,
        ),
      );
    } finally {
      if (streamControllerRef.current === controller) {
        streamControllerRef.current = null;
      }

      setStreamingMessageId((currentId) =>
        currentId === assistantMessageId ? null : currentId,
      );
      setPending(false);
    }
  };

  if (!authReady) {
    return (
      <main className="grid min-h-screen place-items-center bg-gradient-to-br from-[#0b1220] via-[#111827] to-[#020617] px-4 text-white">
        <div className="rounded-[1.5rem] border border-white/10 bg-white/8 px-6 py-5 text-center shadow-[0_20px_60px_rgba(0,0,0,0.24)] backdrop-blur-[18px]">
          <p className="m-0 text-sm font-semibold tracking-[0.12em] uppercase text-white/65">
            Connecting
          </p>
          <p className="mt-2 mb-0 text-lg text-white">
            Checking your Chillazi session...
          </p>
        </div>
      </main>
    );
  }

  if (route.name === "landing") {
    return (
      <LandingPage
        landingHref={landingHref}
        loginHref={loginHref}
        registerHref={registerHref}
        aboutusHref={aboutusHref}
      />
    );
  }
  if (route.name === "about us") {
    return (
      <AboutUsPage
        landingHref={landingHref}
        loginHref={loginHref}
        registerHref={registerHref}
        aboutusHref={aboutusHref}
      />
    );
  }

  if (route.name === "login") {
    return (
      <LoginPage
        error={error}
        landingHref={landingHref}
        mode={route.mode}
        onModeChange={handleModeChange}
        onSubmit={handleAuthSubmit}
        pending={pending}
      />
    );
  }

  if (!session) {
    return (
      <LoginPage
        error={error}
        landingHref={landingHref}
        mode="login"
        onModeChange={handleModeChange}
        onSubmit={handleAuthSubmit}
        pending={pending}
      />
    );
  }

  if (route.name === "admin") {
    return (
      <AdminPage
        chatHref={chatHref}
        landingHref={landingHref}
        onLogout={handleLogout}
        session={session}
      />
    );
  }

  return (
    <ChatPage
      adminHref={session.role === "admin" ? adminHref : undefined}
      landingHref={landingHref}
      messages={messages}
      onLogout={handleLogout}
      onSendMessage={handleSendMessage}
      pending={pending}
      session={session}
      streamingMessageId={streamingMessageId}
    />
  );
}

export default App;
