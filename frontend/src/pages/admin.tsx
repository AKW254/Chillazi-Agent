import { useEffect, useState, type FormEvent } from "react";
import type { UserSession } from "../state";
import {
  clearCart,
  createMenuItem,
  createRole,
  createUser,
  deleteCart,
  deleteMenuItem,
  deleteOrder,
  deleteRole,
  deleteUser,
  listCarts,
  listMenuItems,
  listOrders,
  listRoles,
  listUsers,
  type AdminCart,
  type AdminMenuItem,
  type AdminOrder,
  type AdminOrderStatus,
  type AdminRole,
  type AdminUser,
  resetUserPassword,
  updateMenuItem,
  updateOrderStatus,
  updateRole,
  updateUser,
} from "../services/admin";
import { ApiError } from "../services/http";

type AdminView = "overview" | "orders" | "menu" | "users" | "roles" | "carts";
type NoticeTone = "error" | "success";

interface AdminPageProps {
  chatHref: string;
  landingHref: string;
  onLogout: () => void;
  session: UserSession;
}

interface MenuFormState {
  description: string;
  id: number | null;
  name: string;
  price: string;
}

interface RoleFormState {
  id: number | null;
  name: string;
}

interface UserFormState {
  email: string;
  name: string;
  password: string;
  roleId: string;
}

interface UserDraftState {
  email: string;
  name: string;
  password: string;
  roleId: string;
}

interface NoticeState {
  message: string;
  tone: NoticeTone;
}

const adminViews: Array<{
  description: string;
  id: AdminView;
  label: string;
}> = [
  {
    description: "Platform totals and live operational snapshot.",
    id: "overview",
    label: "Overview",
  },
  {
    description: "Track incoming orders and update their lifecycle.",
    id: "orders",
    label: "Orders",
  },
  {
    description: "Create, edit, and retire menu items.",
    id: "menu",
    label: "Menu",
  },
  {
    description: "Maintain user profiles, roles, and passwords.",
    id: "users",
    label: "Users",
  },
  {
    description: "Manage the role catalog used by the platform.",
    id: "roles",
    label: "Roles",
  },
  {
    description: "Inspect and clean up active customer carts.",
    id: "carts",
    label: "Carts",
  },
];

const orderStatusOptions: AdminOrderStatus[] = [
  "pending",
  "confirmed",
  "preparing",
  "ready",
  "completed",
  "cancelled",
];

function createEmptyMenuForm(): MenuFormState {
  return {
    description: "",
    id: null,
    name: "",
    price: "",
  };
}

function createEmptyRoleForm(): RoleFormState {
  return {
    id: null,
    name: "",
  };
}

function createEmptyUserForm(defaultRoleId = ""): UserFormState {
  return {
    email: "",
    name: "",
    password: "",
    roleId: defaultRoleId,
  };
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-KE", {
    currency: "KES",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    style: "currency",
  }).format(value);
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function sentenceCaseStatus(status: string): string {
  return status.slice(0, 1).toUpperCase() + status.slice(1);
}

function buildUserDrafts(users: AdminUser[]): Record<number, UserDraftState> {
  const drafts: Record<number, UserDraftState> = {};

  for (const user of users) {
    drafts[user.id] = {
      email: user.email,
      name: user.name,
      password: "",
      roleId: String(user.role_id),
    };
  }

  return drafts;
}

function buildOrderStatusDrafts(
  orders: AdminOrder[],
): Record<number, AdminOrderStatus> {
  const drafts: Record<number, AdminOrderStatus> = {};

  for (const order of orders) {
    drafts[order.id] = order.status;
  }

  return drafts;
}

function describeError(
  error: unknown,
  fallbackMessage: string,
): string {
  if (error instanceof ApiError) {
    return error.message || fallbackMessage;
  }

  if (error instanceof Error) {
    return error.message || fallbackMessage;
  }

  return fallbackMessage;
}

function statusToneClasses(status: string): string {
  switch (status) {
    case "completed":
      return "bg-emerald-100 text-emerald-800 border border-emerald-200";
    case "ready":
      return "bg-sky-100 text-sky-800 border border-sky-200";
    case "preparing":
      return "bg-amber-100 text-amber-800 border border-amber-200";
    case "confirmed":
      return "bg-indigo-100 text-indigo-800 border border-indigo-200";
    case "cancelled":
      return "bg-rose-100 text-rose-800 border border-rose-200";
    default:
      return "bg-stone-100 text-stone-800 border border-stone-200";
  }
}

export function AdminPage({
  chatHref,
  landingHref,
  onLogout,
  session,
}: AdminPageProps) {
  const [activeView, setActiveView] = useState<AdminView>("overview");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<NoticeState | null>(null);

  const [menuItems, setMenuItems] = useState<AdminMenuItem[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [carts, setCarts] = useState<AdminCart[]>([]);

  const [menuForm, setMenuForm] = useState<MenuFormState>(createEmptyMenuForm);
  const [roleForm, setRoleForm] = useState<RoleFormState>(createEmptyRoleForm);
  const [userForm, setUserForm] = useState<UserFormState>(() =>
    createEmptyUserForm(""),
  );
  const [userDrafts, setUserDrafts] = useState<Record<number, UserDraftState>>(
    {},
  );
  const [orderStatusDrafts, setOrderStatusDrafts] = useState<
    Record<number, AdminOrderStatus>
  >({});
  const [orderReasonDrafts, setOrderReasonDrafts] = useState<
    Record<number, string>
  >({});

  async function loadDashboard(isInitialLoad = false): Promise<void> {
    if (isInitialLoad) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    try {
      const [
        nextMenuItems,
        nextRoles,
        nextUsers,
        nextOrders,
        nextCarts,
      ] = await Promise.all([
        listMenuItems(session),
        listRoles(session),
        listUsers(session),
        listOrders(session),
        listCarts(session),
      ]);

      setMenuItems(nextMenuItems);
      setRoles(nextRoles);
      setUsers(nextUsers);
      setOrders(nextOrders);
      setCarts(nextCarts);
      setUserDrafts(buildUserDrafts(nextUsers));
      setOrderStatusDrafts(buildOrderStatusDrafts(nextOrders));
      setOrderReasonDrafts({});
      setUserForm((current) =>
        current.roleId ? current : createEmptyUserForm(String(nextRoles[0]?.id ?? "")),
      );
      setError(null);
    } catch (loadError) {
      setError(
        describeError(
          loadError,
          "The dashboard could not load right now. Check your admin access and backend APIs.",
        ),
      );
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  }

  useEffect(() => {
    void loadDashboard(true);
  }, [session]);

  async function runAction(
    actionKey: string,
    successMessage: string,
    action: () => Promise<void>,
  ): Promise<void> {
    setBusyAction(actionKey);
    setNotice(null);
    setError(null);

    try {
      await action();
      setNotice({
        message: successMessage,
        tone: "success",
      });
      await loadDashboard(false);
    } catch (actionError) {
      const message = describeError(
        actionError,
        "That action did not complete successfully.",
      );
      setNotice({
        message,
        tone: "error",
      });
      setError(message);
    } finally {
      setBusyAction(null);
    }
  }

  const currentRoleId = userForm.roleId || String(roles[0]?.id ?? "");
  const totalRevenue = orders.reduce(
    (sum, order) => sum + Number(order.total_amount || 0),
    0,
  );
  const activeCarts = carts.filter((cart) => cart.items.length > 0).length;
  const completedOrders = orders.filter(
    (order) => order.status === "completed",
  ).length;
  const pendingOrders = orders.filter(
    (order) => order.status === "pending" || order.status === "confirmed",
  ).length;

  async function handleMenuSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const price = Number.parseFloat(menuForm.price);
    if (!menuForm.name.trim() || Number.isNaN(price) || price < 0) {
      setNotice({
        message: "Menu name and a valid non-negative price are required.",
        tone: "error",
      });
      return;
    }

    const payload = {
      description: menuForm.description.trim() || null,
      name: menuForm.name.trim(),
      price,
    };

    await runAction(
      menuForm.id ? `menu-update-${menuForm.id}` : "menu-create",
      menuForm.id ? "Menu item updated." : "Menu item created.",
      async () => {
        if (menuForm.id) {
          await updateMenuItem(session, menuForm.id, payload);
        } else {
          await createMenuItem(session, payload);
        }

        setMenuForm(createEmptyMenuForm());
      },
    );
  }

  async function handleRoleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!roleForm.name.trim()) {
      setNotice({
        message: "Role name is required.",
        tone: "error",
      });
      return;
    }

    await runAction(
      roleForm.id ? `role-update-${roleForm.id}` : "role-create",
      roleForm.id ? "Role updated." : "Role created.",
      async () => {
        if (roleForm.id) {
          await updateRole(session, roleForm.id, {
            name: roleForm.name.trim(),
          });
        } else {
          await createRole(session, {
            name: roleForm.name.trim(),
          });
        }

        setRoleForm(createEmptyRoleForm());
      },
    );
  }

  async function handleUserCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (
      !userForm.name.trim() ||
      !userForm.email.trim() ||
      !userForm.password.trim()
    ) {
      setNotice({
        message: "Name, email, and password are required to create a user.",
        tone: "error",
      });
      return;
    }

    await runAction("user-create", "User created.", async () => {
      await createUser(session, {
        email: userForm.email.trim().toLowerCase(),
        name: userForm.name.trim(),
        password: userForm.password,
        role_id: userForm.roleId ? Number(userForm.roleId) : undefined,
      });

      setUserForm(createEmptyUserForm(currentRoleId));
    });
  }

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center px-4 py-8">
        <section className="w-full max-w-xl rounded-[1.8rem] border border-white/12 bg-[rgba(255,248,240,0.14)] p-8 text-white shadow-[0_30px_90px_rgba(0,0,0,0.28)] backdrop-blur-[18px]">
          <p className="m-0 text-xs font-bold tracking-[0.22em] uppercase text-white/60">
            Admin Panel
          </p>
          <h1 className="mt-3 mb-0 font-display text-[clamp(2.6rem,6vw,4.2rem)] leading-none">
            Building the control room.
          </h1>
          <p className="mt-4 mb-0 max-w-lg text-white/76">
            Pulling live menu, user, order, role, and cart data from your Chillazi backend.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-[1600px] px-4 py-5">
      <section className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="grid content-start gap-4 rounded-[1.6rem] border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,24,0.72)] p-5 text-white shadow-[0_28px_90px_rgba(0,0,0,0.22)] backdrop-blur-[18px]">
          <a
            className="inline-flex items-center gap-2 text-sm font-semibold text-white/82 transition hover:text-white"
            href={landingHref}
          >
            <span>{"<"}</span>
            <span>Back to landing</span>
          </a>

          <div className="rounded-[1.4rem] border border-white/10 bg-[rgba(255,255,255,0.05)] p-5">
            <p className="m-0 text-xs font-bold tracking-[0.2em] uppercase text-white/55">
              Chillazi Control
            </p>
            <h1 className="mt-3 mb-0 font-display text-[clamp(2.5rem,4vw,3.8rem)] leading-none">
              Admin
            </h1>
            <p className="mt-3 mb-0 text-sm text-white/74">
              Live operations center for menu, customers, roles, orders, and carts.
            </p>
          </div>

          <div className="rounded-[1.4rem] border border-white/10 bg-[rgba(255,255,255,0.04)] p-5">
            <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-white/52">
              Signed in
            </p>
            <h2 className="mt-2 mb-0 text-xl font-semibold text-white">
              {session.name}
            </h2>
            <p className="mt-1 mb-0 text-sm text-white/68">{session.email}</p>
            <span className="mt-4 inline-flex rounded-full border border-emerald-300/25 bg-emerald-400/12 px-3 py-1 text-xs font-bold tracking-[0.14em] uppercase text-emerald-100">
              {session.role || "admin"}
            </span>
          </div>

          <nav className="grid gap-2">
            {adminViews.map((view) => (
              <button
                className={
                  activeView === view.id
                    ? "grid gap-1 rounded-[1.2rem] border border-[rgba(245,199,174,0.42)] bg-[rgba(203,95,49,0.22)] px-4 py-3 text-left text-white shadow-[0_14px_40px_rgba(157,63,25,0.18)]"
                    : "grid gap-1 rounded-[1.2rem] border border-white/8 bg-[rgba(255,255,255,0.03)] px-4 py-3 text-left text-white/78 transition hover:border-white/16 hover:bg-[rgba(255,255,255,0.06)] hover:text-white"
                }
                key={view.id}
                onClick={() => setActiveView(view.id)}
                type="button"
              >
                <span className="text-sm font-semibold">{view.label}</span>
                <span className="text-xs text-white/58">{view.description}</span>
              </button>
            ))}
          </nav>

          <div className="grid gap-3">
            <a
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/14 bg-white/8 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/14"
              href={chatHref}
            >
              Open Chat Workspace
            </a>
            <button
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-5 py-3 text-sm font-semibold text-sand-50 shadow-[0_14px_28px_rgba(157,63,25,0.28)] transition hover:-translate-y-0.5"
              onClick={onLogout}
              type="button"
            >
              Logout
            </button>
          </div>
        </aside>

        <section className="grid gap-4 rounded-[1.6rem] border border-[rgba(255,249,244,0.1)] bg-[rgba(255,250,246,0.82)] p-5 shadow-[0_28px_80px_rgba(36,24,17,0.16)] backdrop-blur-[18px]">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="m-0 text-xs font-bold tracking-[0.18em] uppercase text-clay-700">
                Operations Dashboard
              </p>
              <h2 className="mt-2 mb-0 font-display text-[clamp(2.4rem,4vw,3.6rem)] leading-none text-espresso-900">
                {adminViews.find((view) => view.id === activeView)?.label}
              </h2>
              <p className="mt-3 mb-0 max-w-2xl text-sm text-[rgba(77,63,54,0.9)]">
                {adminViews.find((view) => view.id === activeView)?.description}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex rounded-full bg-[rgba(255,232,220,0.85)] px-3.5 py-2 text-sm font-bold text-clay-700">
                {refreshing ? "Refreshing..." : "Live backend sync"}
              </span>
              <button
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] bg-white/70 px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-white"
                disabled={refreshing || busyAction !== null}
                onClick={() => void loadDashboard(false)}
                type="button"
              >
                Refresh data
              </button>
            </div>
          </header>

          {notice ? (
            <div
              className={
                notice.tone === "success"
                  ? "rounded-[1.2rem] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
                  : "rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
              }
            >
              {notice.message}
            </div>
          ) : null}

          {error ? (
            <div className="rounded-[1.2rem] border border-[rgba(210,92,48,0.22)] bg-[rgba(255,221,208,0.9)] px-4 py-3 text-sm text-[#7f2300]">
              {error}
            </div>
          ) : null}

          {activeView === "overview" ? (
            <section className="grid gap-4">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <article className="rounded-[1.3rem] border border-[rgba(203,95,49,0.14)] bg-white/80 p-5">
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    Revenue Tracked
                  </p>
                  <h3 className="mt-3 mb-0 text-3xl font-semibold text-espresso-900">
                    {formatCurrency(totalRevenue)}
                  </h3>
                  <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                    Across {orders.length} orders currently stored in the platform.
                  </p>
                </article>

                <article className="rounded-[1.3rem] border border-[rgba(203,95,49,0.14)] bg-white/80 p-5">
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    Order Queue
                  </p>
                  <h3 className="mt-3 mb-0 text-3xl font-semibold text-espresso-900">
                    {pendingOrders}
                  </h3>
                  <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                    Pending or confirmed orders waiting on the kitchen flow.
                  </p>
                </article>

                <article className="rounded-[1.3rem] border border-[rgba(203,95,49,0.14)] bg-white/80 p-5">
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    Completed Orders
                  </p>
                  <h3 className="mt-3 mb-0 text-3xl font-semibold text-espresso-900">
                    {completedOrders}
                  </h3>
                  <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                    Orders that have reached the finish line successfully.
                  </p>
                </article>

                <article className="rounded-[1.3rem] border border-[rgba(203,95,49,0.14)] bg-white/80 p-5">
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    Active Carts
                  </p>
                  <h3 className="mt-3 mb-0 text-3xl font-semibold text-espresso-900">
                    {activeCarts}
                  </h3>
                  <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                    Customer carts that still contain items and may need follow-up.
                  </p>
                </article>
              </div>

              <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
                <section className="rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/80 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                        Recent Orders
                      </p>
                      <h3 className="mt-2 mb-0 text-xl font-semibold text-espresso-900">
                        Live service board
                      </h3>
                    </div>
                    <button
                      className="rounded-full border border-[rgba(116,78,51,0.14)] px-3 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                      onClick={() => setActiveView("orders")}
                      type="button"
                    >
                      Open orders
                    </button>
                  </div>

                  <div className="mt-4 overflow-hidden rounded-[1.2rem] border border-[rgba(116,78,51,0.08)]">
                    <table className="min-w-full border-collapse">
                      <thead className="bg-[rgba(245,241,229,0.72)] text-left text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                        <tr>
                          <th className="px-4 py-3">Order</th>
                          <th className="px-4 py-3">User</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Total</th>
                          <th className="px-4 py-3">Created</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white/80 text-sm text-espresso-900">
                        {orders.slice(0, 6).map((order) => (
                          <tr
                            className="border-t border-[rgba(116,78,51,0.08)]"
                            key={order.id}
                          >
                            <td className="px-4 py-3 font-semibold">#{order.id}</td>
                            <td className="px-4 py-3">User {order.user_id}</td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${statusToneClasses(order.status)}`}
                              >
                                {sentenceCaseStatus(order.status)}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              {formatCurrency(order.total_amount)}
                            </td>
                            <td className="px-4 py-3">
                              {formatDateTime(order.created_at)}
                            </td>
                          </tr>
                        ))}
                        {orders.length === 0 ? (
                          <tr>
                            <td
                              className="px-4 py-6 text-center text-[rgba(77,63,54,0.72)]"
                              colSpan={5}
                            >
                              No orders yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="grid gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/80 p-5">
                  <div>
                    <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                      Platform Inventory
                    </p>
                    <h3 className="mt-2 mb-0 text-xl font-semibold text-espresso-900">
                      Core records
                    </h3>
                  </div>

                  <div className="grid gap-3">
                    <article className="rounded-[1.1rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/70 px-4 py-4">
                      <p className="m-0 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                        Menu items
                      </p>
                      <p className="mt-2 mb-0 text-2xl font-semibold text-espresso-900">
                        {menuItems.length}
                      </p>
                    </article>
                    <article className="rounded-[1.1rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/70 px-4 py-4">
                      <p className="m-0 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                        Users
                      </p>
                      <p className="mt-2 mb-0 text-2xl font-semibold text-espresso-900">
                        {users.length}
                      </p>
                    </article>
                    <article className="rounded-[1.1rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/70 px-4 py-4">
                      <p className="m-0 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                        Roles
                      </p>
                      <p className="mt-2 mb-0 text-2xl font-semibold text-espresso-900">
                        {roles.length}
                      </p>
                    </article>
                    <article className="rounded-[1.1rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/70 px-4 py-4">
                      <p className="m-0 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                        Carts
                      </p>
                      <p className="mt-2 mb-0 text-2xl font-semibold text-espresso-900">
                        {carts.length}
                      </p>
                    </article>
                  </div>
                </section>
              </div>
            </section>
          ) : null}

          {activeView === "orders" ? (
            <section className="grid gap-4">
              {orders.map((order) => (
                <article
                  className="grid gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5"
                  key={order.id}
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="m-0 text-xl font-semibold text-espresso-900">
                          Order #{order.id}
                        </h3>
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${statusToneClasses(order.status)}`}
                        >
                          {sentenceCaseStatus(order.status)}
                        </span>
                      </div>
                      <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.82)]">
                        User {order.user_id} · {order.item_count} items ·{" "}
                        {formatCurrency(order.total_amount)} ·{" "}
                        {formatDateTime(order.created_at)}
                      </p>
                      {order.delivery_address ? (
                        <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.76)]">
                          Delivery: {order.delivery_address}
                        </p>
                      ) : null}
                      {order.notes ? (
                        <p className="mt-1 mb-0 text-sm text-[rgba(77,63,54,0.76)]">
                          Notes: {order.notes}
                        </p>
                      ) : null}
                    </div>

                    <div className="grid gap-3 lg:min-w-[360px]">
                      <select
                        className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-sm text-espresso-900 outline-none"
                        onChange={(event) =>
                          setOrderStatusDrafts((current) => ({
                            ...current,
                            [order.id]: event.target.value as AdminOrderStatus,
                          }))
                        }
                        value={orderStatusDrafts[order.id] ?? order.status}
                      >
                        {orderStatusOptions.map((status) => (
                          <option key={status} value={status}>
                            {sentenceCaseStatus(status)}
                          </option>
                        ))}
                      </select>
                      <input
                        className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-sm text-espresso-900 outline-none"
                        onChange={(event) =>
                          setOrderReasonDrafts((current) => ({
                            ...current,
                            [order.id]: event.target.value,
                          }))
                        }
                        placeholder="Reason for status change"
                        value={orderReasonDrafts[order.id] ?? ""}
                      />
                      <div className="flex flex-wrap gap-3">
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-4 py-2 text-sm font-semibold text-sand-50 shadow-[0_12px_24px_rgba(157,63,25,0.18)]"
                          disabled={busyAction !== null}
                          onClick={() =>
                            void runAction(
                              `order-status-${order.id}`,
                              `Order #${order.id} updated.`,
                              async () => {
                                await updateOrderStatus(session, order.id, {
                                  reason:
                                    orderReasonDrafts[order.id]?.trim() || null,
                                  status:
                                    orderStatusDrafts[order.id] ?? order.status,
                                });
                              },
                            )
                          }
                          type="button"
                        >
                          Update status
                        </button>
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
                          disabled={busyAction !== null}
                          onClick={() =>
                            void runAction(
                              `order-delete-${order.id}`,
                              `Order #${order.id} deleted.`,
                              async () => {
                                await deleteOrder(session, order.id);
                              },
                            )
                          }
                          type="button"
                        >
                          Delete order
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {(order.items ?? []).length > 0 ? (
                      (order.items ?? []).map((item) => (
                        <div
                          className="rounded-[1.1rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/72 px-4 py-4"
                          key={item.id}
                        >
                          <p className="m-0 text-sm font-semibold text-espresso-900">
                            {item.menu_item?.name || `Item #${item.menu_item_id}`}
                          </p>
                          <p className="mt-1 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                            Qty {item.quantity}
                            {item.menu_item
                              ? ` · ${formatCurrency(item.menu_item.price)}`
                              : ""}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-[1.1rem] border border-dashed border-[rgba(116,78,51,0.16)] bg-sand-50/52 px-4 py-5 text-sm text-[rgba(77,63,54,0.72)]">
                        Order details are available after a direct detail refresh.
                      </div>
                    )}
                  </div>
                </article>
              ))}

              {orders.length === 0 ? (
                <div className="rounded-[1.35rem] border border-dashed border-[rgba(116,78,51,0.18)] bg-white/75 px-5 py-10 text-center text-[rgba(77,63,54,0.72)]">
                  No orders found.
                </div>
              ) : null}
            </section>
          ) : null}

          {activeView === "menu" ? (
            <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
              <form
                className="grid content-start gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5"
                onSubmit={(event) => void handleMenuSubmit(event)}
              >
                <div>
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    {menuForm.id ? "Edit item" : "Create item"}
                  </p>
                  <h3 className="mt-2 mb-0 text-xl font-semibold text-espresso-900">
                    Menu builder
                  </h3>
                </div>

                <label className="grid gap-2">
                  <span className="text-sm font-semibold text-espresso-900">Name</span>
                  <input
                    className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                    onChange={(event) =>
                      setMenuForm((current) => ({
                        ...current,
                        name: event.target.value,
                      }))
                    }
                    value={menuForm.name}
                  />
                </label>

                <label className="grid gap-2">
                  <span className="text-sm font-semibold text-espresso-900">
                    Description
                  </span>
                  <textarea
                    className="min-h-28 rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                    onChange={(event) =>
                      setMenuForm((current) => ({
                        ...current,
                        description: event.target.value,
                      }))
                    }
                    value={menuForm.description}
                  />
                </label>

                <label className="grid gap-2">
                  <span className="text-sm font-semibold text-espresso-900">Price</span>
                  <input
                    className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                    min="0"
                    onChange={(event) =>
                      setMenuForm((current) => ({
                        ...current,
                        price: event.target.value,
                      }))
                    }
                    step="0.01"
                    type="number"
                    value={menuForm.price}
                  />
                </label>

                <div className="flex flex-wrap gap-3">
                  <button
                    className="inline-flex min-h-11 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-4 py-2 text-sm font-semibold text-sand-50 shadow-[0_12px_24px_rgba(157,63,25,0.18)]"
                    disabled={busyAction !== null}
                    type="submit"
                  >
                    {menuForm.id ? "Save item" : "Create item"}
                  </button>
                  {menuForm.id ? (
                    <button
                      className="inline-flex min-h-11 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                      onClick={() => setMenuForm(createEmptyMenuForm())}
                      type="button"
                    >
                      Cancel edit
                    </button>
                  ) : null}
                </div>
              </form>

              <div className="grid gap-4">
                {menuItems.map((item) => (
                  <article
                    className="flex flex-col gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5 md:flex-row md:items-start md:justify-between"
                    key={item.id}
                  >
                    <div>
                      <h3 className="m-0 text-lg font-semibold text-espresso-900">
                        {item.name}
                      </h3>
                      <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.78)]">
                        {item.description || "No description added yet."}
                      </p>
                      <p className="mt-3 mb-0 text-sm font-semibold text-clay-700">
                        {formatCurrency(item.price)}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        className="rounded-full border border-[rgba(116,78,51,0.14)] px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                        onClick={() =>
                          setMenuForm({
                            description: item.description || "",
                            id: item.id,
                            name: item.name,
                            price: String(item.price),
                          })
                        }
                        type="button"
                      >
                        Edit
                      </button>
                      <button
                        className="rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
                        disabled={busyAction !== null}
                        onClick={() =>
                          void runAction(
                            `menu-delete-${item.id}`,
                            `${item.name} deleted from the menu.`,
                            async () => {
                              await deleteMenuItem(session, item.id);
                            },
                          )
                        }
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}

          {activeView === "users" ? (
            <section className="grid gap-4">
              <form
                className="grid gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5 xl:grid-cols-[1.1fr_1.1fr_1fr_0.9fr_auto]"
                onSubmit={(event) => void handleUserCreate(event)}
              >
                <div>
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    Invite user
                  </p>
                  <h3 className="mt-2 mb-0 text-xl font-semibold text-espresso-900">
                    Create account
                  </h3>
                </div>
                <input
                  className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                  onChange={(event) =>
                    setUserForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="Full name"
                  value={userForm.name}
                />
                <input
                  className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                  onChange={(event) =>
                    setUserForm((current) => ({
                      ...current,
                      email: event.target.value,
                    }))
                  }
                  placeholder="Email address"
                  type="email"
                  value={userForm.email}
                />
                <input
                  className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                  onChange={(event) =>
                    setUserForm((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  placeholder="Temporary password"
                  type="password"
                  value={userForm.password}
                />
                <div className="flex flex-wrap gap-3">
                  <select
                    className="min-w-[150px] rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                    onChange={(event) =>
                      setUserForm((current) => ({
                        ...current,
                        roleId: event.target.value,
                      }))
                    }
                    value={userForm.roleId || currentRoleId}
                  >
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                  <button
                    className="inline-flex min-h-11 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-4 py-2 text-sm font-semibold text-sand-50 shadow-[0_12px_24px_rgba(157,63,25,0.18)]"
                    disabled={busyAction !== null}
                    type="submit"
                  >
                    Create user
                  </button>
                </div>
              </form>

              <div className="grid gap-4">
                {users.map((user) => {
                  const draft = userDrafts[user.id] ?? {
                    email: user.email,
                    name: user.name,
                    password: "",
                    roleId: String(user.role_id),
                  };

                  return (
                    <article
                      className="grid gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5"
                      key={user.id}
                    >
                      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <h3 className="m-0 text-lg font-semibold text-espresso-900">
                            {user.name}
                            {user.id === session.id ? " (you)" : ""}
                          </h3>
                          <p className="mt-1 mb-0 text-sm text-[rgba(77,63,54,0.76)]">
                            #{user.id} · {user.email} · {user.role_name || "No role"}
                          </p>
                        </div>
                        <span className="inline-flex w-fit rounded-full bg-[rgba(255,232,220,0.8)] px-3 py-1 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                          Role #{user.role_id}
                        </span>
                      </div>

                      <div className="grid gap-3 xl:grid-cols-[1fr_1fr_220px_auto_auto]">
                        <input
                          className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                          onChange={(event) =>
                            setUserDrafts((current) => ({
                              ...current,
                              [user.id]: {
                                ...draft,
                                name: event.target.value,
                              },
                            }))
                          }
                          value={draft.name}
                        />
                        <input
                          className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                          onChange={(event) =>
                            setUserDrafts((current) => ({
                              ...current,
                              [user.id]: {
                                ...draft,
                                email: event.target.value,
                              },
                            }))
                          }
                          type="email"
                          value={draft.email}
                        />
                        <select
                          className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                          onChange={(event) =>
                            setUserDrafts((current) => ({
                              ...current,
                              [user.id]: {
                                ...draft,
                                roleId: event.target.value,
                              },
                            }))
                          }
                          value={draft.roleId}
                        >
                          {roles.map((role) => (
                            <option key={role.id} value={role.id}>
                              {role.name}
                            </option>
                          ))}
                        </select>
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-4 py-2 text-sm font-semibold text-sand-50 shadow-[0_12px_24px_rgba(157,63,25,0.18)]"
                          disabled={busyAction !== null}
                          onClick={() =>
                            void runAction(
                              `user-save-${user.id}`,
                              `User #${user.id} updated.`,
                              async () => {
                                await updateUser(session, user.id, {
                                  email: draft.email.trim().toLowerCase(),
                                  name: draft.name.trim(),
                                  role_id: Number(draft.roleId),
                                });
                              },
                            )
                          }
                          type="button"
                        >
                          Save
                        </button>
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busyAction !== null || user.id === session.id}
                          onClick={() =>
                            void runAction(
                              `user-delete-${user.id}`,
                              `User #${user.id} deleted.`,
                              async () => {
                                await deleteUser(session, user.id);
                              },
                            )
                          }
                          type="button"
                        >
                          Delete
                        </button>
                      </div>

                      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_auto]">
                        <input
                          className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                          onChange={(event) =>
                            setUserDrafts((current) => ({
                              ...current,
                              [user.id]: {
                                ...draft,
                                password: event.target.value,
                              },
                            }))
                          }
                          placeholder="New password for reset"
                          type="password"
                          value={draft.password}
                        />
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] bg-white px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                          disabled={busyAction !== null || !draft.password.trim()}
                          onClick={() =>
                            void runAction(
                              `user-password-${user.id}`,
                              `Password reset for user #${user.id}.`,
                              async () => {
                                await resetUserPassword(
                                  session,
                                  user.id,
                                  draft.password.trim(),
                                );
                                setUserDrafts((current) => ({
                                  ...current,
                                  [user.id]: {
                                    ...draft,
                                    password: "",
                                  },
                                }));
                              },
                            )
                          }
                          type="button"
                        >
                          Reset password
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          ) : null}

          {activeView === "roles" ? (
            <section className="grid gap-4 xl:grid-cols-[340px_minmax(0,1fr)]">
              <form
                className="grid content-start gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5"
                onSubmit={(event) => void handleRoleSubmit(event)}
              >
                <div>
                  <p className="m-0 text-xs font-bold tracking-[0.16em] uppercase text-clay-700">
                    {roleForm.id ? "Edit role" : "Create role"}
                  </p>
                  <h3 className="mt-2 mb-0 text-xl font-semibold text-espresso-900">
                    Role registry
                  </h3>
                </div>

                <input
                  className="rounded-2xl border border-[rgba(116,78,51,0.14)] bg-white px-4 py-3 text-espresso-900 outline-none"
                  onChange={(event) =>
                    setRoleForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="Role name"
                  value={roleForm.name}
                />

                <div className="flex flex-wrap gap-3">
                  <button
                    className="inline-flex min-h-11 items-center justify-center rounded-full bg-linear-to-br from-clay-500 to-clay-700 px-4 py-2 text-sm font-semibold text-sand-50 shadow-[0_12px_24px_rgba(157,63,25,0.18)]"
                    disabled={busyAction !== null}
                    type="submit"
                  >
                    {roleForm.id ? "Save role" : "Create role"}
                  </button>
                  {roleForm.id ? (
                    <button
                      className="inline-flex min-h-11 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                      onClick={() => setRoleForm(createEmptyRoleForm())}
                      type="button"
                    >
                      Cancel edit
                    </button>
                  ) : null}
                </div>
              </form>

              <div className="grid gap-4">
                {roles.map((role) => (
                  <article
                    className="flex flex-col gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5 md:flex-row md:items-center md:justify-between"
                    key={role.id}
                  >
                    <div>
                      <h3 className="m-0 text-lg font-semibold text-espresso-900">
                        {role.name}
                      </h3>
                      <p className="mt-1 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                        Role ID #{role.id}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      <button
                        className="rounded-full border border-[rgba(116,78,51,0.14)] px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50"
                        onClick={() =>
                          setRoleForm({
                            id: role.id,
                            name: role.name,
                          })
                        }
                        type="button"
                      >
                        Edit
                      </button>
                      <button
                        className="rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
                        disabled={busyAction !== null}
                        onClick={() =>
                          void runAction(
                            `role-delete-${role.id}`,
                            `Role ${role.name} deleted.`,
                            async () => {
                              await deleteRole(session, role.id);
                            },
                          )
                        }
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}

          {activeView === "carts" ? (
            <section className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              {carts.map((cart) => (
                <article
                  className="grid gap-4 rounded-[1.35rem] border border-[rgba(116,78,51,0.1)] bg-white/82 p-5"
                  key={cart.id}
                >
                  <div>
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="m-0 text-lg font-semibold text-espresso-900">
                        Cart #{cart.id}
                      </h3>
                      <span className="inline-flex rounded-full bg-[rgba(255,232,220,0.8)] px-3 py-1 text-xs font-bold tracking-[0.14em] uppercase text-clay-700">
                        User {cart.user_id}
                      </span>
                    </div>
                    <p className="mt-2 mb-0 text-sm text-[rgba(77,63,54,0.78)]">
                      {cart.items.length} items · {formatCurrency(cart.total_amount)} ·{" "}
                      {formatDateTime(cart.created_at)}
                    </p>
                  </div>

                  <div className="grid gap-3">
                    {cart.items.length > 0 ? (
                      cart.items.map((item) => (
                        <div
                          className="rounded-[1.05rem] border border-[rgba(116,78,51,0.08)] bg-sand-50/72 px-4 py-3"
                          key={item.id}
                        >
                          <p className="m-0 text-sm font-semibold text-espresso-900">
                            {item.menu_item?.name || `Item #${item.menu_item_id}`}
                          </p>
                          <p className="mt-1 mb-0 text-sm text-[rgba(77,63,54,0.72)]">
                            Qty {item.quantity}
                            {item.menu_item
                              ? ` · ${formatCurrency(item.menu_item.price)}`
                              : ""}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-[1.05rem] border border-dashed border-[rgba(116,78,51,0.16)] bg-sand-50/52 px-4 py-4 text-sm text-[rgba(77,63,54,0.72)]">
                        This cart is currently empty.
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <button
                      className="inline-flex min-h-11 items-center justify-center rounded-full border border-[rgba(116,78,51,0.14)] bg-white px-4 py-2 text-sm font-semibold text-espresso-900 transition hover:bg-sand-50 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={busyAction !== null || cart.items.length === 0}
                      onClick={() =>
                        void runAction(
                          `cart-clear-${cart.id}`,
                          `Cart #${cart.id} cleared.`,
                          async () => {
                            await clearCart(session, cart.id);
                          },
                        )
                      }
                      type="button"
                    >
                      Clear cart
                    </button>
                    <button
                      className="inline-flex min-h-11 items-center justify-center rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
                      disabled={busyAction !== null}
                      onClick={() =>
                        void runAction(
                          `cart-delete-${cart.id}`,
                          `Cart #${cart.id} deleted.`,
                          async () => {
                            await deleteCart(session, cart.id);
                          },
                        )
                      }
                      type="button"
                    >
                      Delete cart
                    </button>
                  </div>
                </article>
              ))}

              {carts.length === 0 ? (
                <div className="rounded-[1.35rem] border border-dashed border-[rgba(116,78,51,0.18)] bg-white/75 px-5 py-10 text-center text-[rgba(77,63,54,0.72)]">
                  No carts found.
                </div>
              ) : null}
            </section>
          ) : null}
        </section>
      </section>
    </main>
  );
}
