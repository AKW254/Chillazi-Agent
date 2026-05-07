import { useEffect, useState, type FormEvent } from "react";
import type { AuthMode, AuthPayload } from "../state";

interface LoginPageProps {
  error: string | null;
  landingHref: string;
  mode: AuthMode;
  onModeChange: (mode: AuthMode) => void;
  onSubmit: (mode: AuthMode, payload: AuthPayload) => Promise<void>;
  pending: boolean;
}

export function LoginPage({
  error,
  landingHref,
  mode,
  onModeChange,
  onSubmit,
  pending,
}: LoginPageProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (mode === "login") setFullName("");
  }, [mode]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit(mode, { fullName, email, password });
  };

  return (
    <main className="grid min-h-screen items-center bg-gradient-to-br from-[#0b1220] via-[#111827] to-[#020617] text-white">
      <section
        className={`
          mx-auto grid w-full max-w-6xl
          animate-[fade-up_0.7s_ease_both]
          bg-gradient-to-br from-[rgba(255,241,231,0.86)] to-white/66
          rounded-[1.75rem]
          gap-8
          p-5
          shadow-[0_28px_80px_rgba(98,49,16,0.14)]      ← arbitrary, no exact theme match
          backdrop-blur-[18px]
          lg:grid-cols-[minmax(0,0.95fr)_minmax(340px,1.05fr)]
          lg:p-7
        `}
      >
        {/* ---------- LEFT PANEL ---------- */}
        <div
          className={`
            grid content-start gap-4 rounded-[1.55rem]
            bg-gradient-to-b from-[rgba(255,241,231,0.86)] to-white/66
            p-5 lg:p-6
          `}
        >
          <a
            className="inline-flex items-center gap-2 font-semibold text-clay-700"
            href={landingHref}
          >
            <span>{"<"}</span>
            <span>Back to landing</span>
          </a>
          <p className="m-0 text-xs font-bold tracking-[0.16em] text-clay-700 uppercase">
            Secure access scaffold
          </p>
          <h1 className="m-0 font-display text-[clamp(3rem,6vw,5rem)] leading-[0.96] font-normal tracking-[-0.04em] text-espresso-900">
            {mode === "login"
              ? "Welcome back to Chillazi."
              : "Create your Chillazi account."}
          </h1>
          <p className="m-0 text-espresso-900/70">
            {" "}
            {/* rgba(107,92,80,1) ≈ espresso with slight opacity */}
            The auth screen is intentionally shared for both flows, so you can
            keep one clean entry point while wiring it to your real backend
            later.
          </p>

          {/* Tip box */}
          <div
            className={`
              rounded-[1.5rem] border border-clay-500/12          ← exact rgba(203,95,49,0.12)
              bg-gradient-to-br from-white/86 to-sand-100/72      ← sand-100 ≈ #f7f1e5, close to rgba(255,243,233)
              p-5
            `}
          >
            <strong className="mb-1 block text-espresso-900">
              Starter tip
            </strong>
            <p className="m-0 text-espresso-900/70">
              Register with any email and password, then use the same email
              later to simulate a returning login.
            </p>
          </div>
        </div>

        {/* ---------- RIGHT PANEL ---------- */}
        <div
          className={`
            rounded-[1.55rem]
            border border-clay-700/10                    ← rgba(116,78,51,0.1)
            bg-sand-50/74                                ← sand-50 with 74% opacity
            p-5 lg:p-6
          `}
        >
          {/* Toggle tabs */}
          <div
            className="grid grid-cols-2 gap-2 rounded-full bg-sand-200/55 p-1.5" // sand-200 ≈ #ead8c3, 55% opacity
            role="tablist"
            aria-label="Authentication mode"
          >
            <button
              className={
                mode === "login"
                  ? "min-h-11 rounded-full bg-sand-50 px-4 text-sm font-semibold text-clay-600 shadow-[0_10px_24px_rgba(116,78,51,0.1)]"
                  : "min-h-11 rounded-full bg-transparent px-4 text-sm font-semibold text-espresso-900/50 hover:text-espresso-900/80"
              }
              onClick={() => onModeChange("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={
                mode === "register"
                  ? "min-h-11 rounded-full bg-sand-50 px-4 text-sm font-semibold text-clay-600 shadow-[0_10px_24px_rgba(116,78,51,0.1)]"
                  : "min-h-11 rounded-full bg-transparent px-4 text-sm font-semibold text-espresso-900/50 hover:text-espresso-900/80"
              }
              onClick={() => onModeChange("register")}
              type="button"
            >
              Register
            </button>
          </div>

          <form className="mt-5 grid gap-4" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label className="grid gap-2">
                <span className="text-sm font-semibold text-espresso-900">
                  Full name
                </span>
                <input
                  autoComplete="name"
                  className="w-full rounded-2xl border border-clay-700/14 bg-white/82 px-4 py-3 text-espresso-900 outline-none transition focus:border-clay-500/60 focus:shadow-[0_0_0_4px_rgba(203,95,49,0.12)]"
                  name="fullName"
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Amina Wanjiku"
                  required={mode === "register"}
                  value={fullName}
                />
              </label>
            )}

            <label className="grid gap-2">
              <span className="text-sm font-semibold text-espresso-900">
                Email address
              </span>
              <input
                autoComplete="email"
                className="w-full rounded-2xl border border-clay-700/14 bg-white/82 px-4 py-3 text-espresso-900 outline-none transition focus:border-clay-500/60 focus:shadow-[0_0_0_4px_rgba(203,95,49,0.12)]"
                name="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="guest@chillazi.com"
                required
                type="email"
                value={email}
              />
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-semibold text-espresso-900">
                Password
              </span>
              <input
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                className="w-full rounded-2xl border border-clay-700/14 bg-white/82 px-4 py-3 text-espresso-900 outline-none transition focus:border-clay-500/60 focus:shadow-[0_0_0_4px_rgba(203,95,49,0.12)]"
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter a secure password"
                required
                type="password"
                value={password}
              />
            </label>

            {error && (
              <p className="m-0 rounded-2xl border border-[rgba(210,92,48,0.22)] bg-[rgba(255,221,208,0.9)] px-4 py-3 text-sm text-[#7f2300]">
                {error}
              </p>
            )}

            <button
              className="mt-2 rounded-full bg-clay-600 px-4 py-3 font-medium text-white shadow-lg shadow-clay-500/20 transition hover:bg-clay-700 disabled:cursor-not-allowed disabled:bg-clay-600/70"
              disabled={pending}
              type="submit"
            >
              {pending
                ? mode === "login"
                  ? "Signing in..."
                  : "Creating account..."
                : mode === "login"
                  ? "Login"
                  : "Register"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
