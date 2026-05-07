// router.ts
// ---------
// Hash‑based router for a React app (Tailwind v4 + TypeScript).
// Add new routes by extending the `ROUTES` object – no other changes needed.

import type { AuthMode } from "./state";

// ---------------------------------------------------
// Types
// ---------------------------------------------------

export type AppRoute =
  | { name: "landing" }
  | { name: "about us" }
  | { name: "login"; mode: AuthMode }
  | { name: "admin" }
  | { name: "chat" }
  | { name: "profile" }
  | { name: "settings" };

// ---------------------------------------------------
// Route map – single source of truth
// ---------------------------------------------------

type RouteDefinition = {
  /** URL hash path (e.g. '/profile') */
  path: string;
  /** Create the AppRoute object for this route */
  build: () => AppRoute;
  /** True if the route requires authentication */
  isProtected: boolean;
  /** True if the route requires admin privileges */
  requiresAdmin?: boolean;
};

/**
 * All known application routes.
 *
 * To add a new route:
 * 1. Add its name to the `AppRoute` type above.
 * 2. Add a new entry here with its path, `build` function, and `isProtected` flag.
 *
 * Auth routes (login/register) are handled separately because they carry a `mode`.
 */
const ROUTES: Record<string, RouteDefinition> = {
  landing: {
    path: "/",
    build: () => ({ name: "landing" }),
    isProtected: false,
  },
  "about us": {
    path: "/about-us",
    build: () => ({ name: "about us" }),
    isProtected: false,
  },
  chat: {
    path: "/chat",
    build: () => ({ name: "chat" }),
    isProtected: true,
  },
  admin: {
    path: "/admin",
    build: () => ({ name: "admin" }),
    isProtected: true,
    requiresAdmin: true,
  },
  profile: {
    path: "/profile",
    build: () => ({ name: "profile" }),
    isProtected: true,
  },
  settings: {
    path: "/settings",
    build: () => ({ name: "settings" }),
    isProtected: true,
  },
};

// ---------------------------------------------------
// Normalize hash helper
// ---------------------------------------------------

/**
 * Cleans a raw URL hash and ensures it starts with '/'.
 * Returns '/' if the hash is empty.
 */
function normalizeHash(rawHash: string): string {
  const cleaned = rawHash.replace(/^#/, "").trim();
  if (!cleaned) return "/";
  return cleaned.startsWith("/") ? cleaned : `/${cleaned}`;
}

// ---------------------------------------------------
// Route resolution
// ---------------------------------------------------

/**
 * Converts the current URL hash (and authentication state) into an `AppRoute`.
 *
 * Rules:
 * - /login or /register           → login page (with appropriate mode), unless already authenticated → chat
 * - Any protected route (chat, profile, …) → login page if not authenticated
 * - Unknown paths                → landing page
 */
function defaultAuthenticatedRoute(isAdmin: boolean): AppRoute {
  return isAdmin ? ROUTES.admin.build() : ROUTES.chat.build();
}

export function resolveRoute(
  hash: string,
  isAuthenticated: boolean,
  isAdmin = false,
): AppRoute {
  const path = normalizeHash(hash);

  // ---- Auth-specific routes (have a `mode`) ----
  if (path === "/login") {
    return isAuthenticated
      ? defaultAuthenticatedRoute(isAdmin)
      : { name: "login", mode: "login" };
  }
  if (path === "/register") {
    return isAuthenticated
      ? defaultAuthenticatedRoute(isAdmin)
      : { name: "login", mode: "register" };
  }

  // ---- All other routes ----
  const routeEntry = Object.values(ROUTES).find((r) => r.path === path);

  if (routeEntry) {
    if (routeEntry.isProtected && !isAuthenticated) {
      // Redirect to login (default mode) if not authenticated
      return { name: "login", mode: "login" };
    }
    if (routeEntry.requiresAdmin && !isAdmin) {
      return isAuthenticated ? ROUTES.chat.build() : { name: "login", mode: "login" };
    }
    return routeEntry.build();
  }

  // Fallback for unknown paths
  return { name: "landing" };
}

// ---------------------------------------------------
// Build hash from route
// ---------------------------------------------------

/**
 * Returns the URL hash (e.g. '#/settings') for a given `AppRoute`.
 */
export function buildHref(route: AppRoute): string {
  // Auth routes are special because they can be login or register
  if (route.name === "login") {
    return route.mode === "register" ? "#/register" : "#/login";
  }

  const routeEntry = ROUTES[route.name];
  return routeEntry ? `#${routeEntry.path}` : "#/";
}

// ---------------------------------------------------
// Programmatic navigation
// ---------------------------------------------------

/**
 * Updates `window.location.hash` to navigate to `route`,
 * but only if the target hash differs from the current one.
 */
export function navigateTo(route: AppRoute): void {
  const target = buildHref(route);
  if (window.location.hash !== target) {
    window.location.hash = target;
  }
}
