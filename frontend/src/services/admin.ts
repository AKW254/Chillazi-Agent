import type { UserSession } from "../state";
import {
  createAuthHeaders,
  createJsonHeaders,
  requestJson,
} from "./http";

export type AdminOrderStatus =
  | "pending"
  | "confirmed"
  | "preparing"
  | "ready"
  | "completed"
  | "cancelled";

export interface AdminMenuItem {
  description: string | null;
  id: number;
  name: string;
  price: number;
}

export interface AdminRole {
  id: number;
  name: string;
}

export interface AdminUser {
  email: string;
  id: number;
  name: string;
  role_id: number;
  role_name: string | null;
}

export interface AdminOrderItem {
  id: number;
  menu_item: AdminMenuItem | null;
  menu_item_id: number;
  quantity: number;
}

export interface AdminOrder {
  created_at: string;
  delivery_address?: string | null;
  id: number;
  item_count: number;
  items?: AdminOrderItem[];
  notes?: string | null;
  status: AdminOrderStatus;
  total_amount: number;
  user_id: number;
}

export interface AdminCartItem {
  id: number;
  menu_item: AdminMenuItem | null;
  menu_item_id: number;
  quantity: number;
}

export interface AdminCart {
  created_at: string;
  id: number;
  items: AdminCartItem[];
  total_amount: number;
  user_id: number;
}

export interface MenuItemInput {
  description?: string | null;
  name: string;
  price: number;
}

export interface RoleInput {
  name: string;
}

export interface UserUpdateInput {
  email?: string;
  name?: string;
  role_id?: number;
}

export interface CreateUserInput {
  email: string;
  name: string;
  password: string;
  role_id?: number;
}

export interface OrderStatusUpdateInput {
  reason?: string | null;
  status: AdminOrderStatus;
}

function authHeaders(session: UserSession): Headers {
  return createAuthHeaders(session.accessToken);
}

function jsonAuthHeaders(session: UserSession): Headers {
  return createAuthHeaders(session.accessToken, createJsonHeaders());
}

export async function listMenuItems(session: UserSession): Promise<AdminMenuItem[]> {
  return requestJson<AdminMenuItem[]>("/api/menu/", {
    headers: authHeaders(session),
    method: "GET",
  });
}

export async function createMenuItem(
  session: UserSession,
  input: MenuItemInput,
): Promise<AdminMenuItem> {
  return requestJson<AdminMenuItem>("/api/menu/", {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "POST",
  });
}

export async function updateMenuItem(
  session: UserSession,
  itemId: number,
  input: MenuItemInput,
): Promise<AdminMenuItem> {
  return requestJson<AdminMenuItem>(`/api/menu/${itemId}`, {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "PUT",
  });
}

export async function deleteMenuItem(
  session: UserSession,
  itemId: number,
): Promise<void> {
  await requestJson(`/api/menu/${itemId}`, {
    headers: authHeaders(session),
    method: "DELETE",
  });
}

export async function listRoles(session: UserSession): Promise<AdminRole[]> {
  return requestJson<AdminRole[]>("/api/roles/", {
    headers: authHeaders(session),
    method: "GET",
  });
}

export async function createRole(
  session: UserSession,
  input: RoleInput,
): Promise<AdminRole> {
  return requestJson<AdminRole>("/api/roles/", {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "POST",
  });
}

export async function updateRole(
  session: UserSession,
  roleId: number,
  input: RoleInput,
): Promise<AdminRole> {
  return requestJson<AdminRole>(`/api/roles/${roleId}`, {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "PUT",
  });
}

export async function deleteRole(
  session: UserSession,
  roleId: number,
): Promise<void> {
  await requestJson(`/api/roles/${roleId}`, {
    headers: authHeaders(session),
    method: "DELETE",
  });
}

export async function listUsers(session: UserSession): Promise<AdminUser[]> {
  return requestJson<AdminUser[]>("/api/users/", {
    headers: authHeaders(session),
    method: "GET",
  });
}

export async function createUser(
  session: UserSession,
  input: CreateUserInput,
): Promise<AdminUser> {
  const createdUser = await requestJson<AdminUser>("/api/users/", {
    body: JSON.stringify({
      email: input.email,
      name: input.name,
      password: input.password,
    }),
    headers: createJsonHeaders(),
    method: "POST",
  });

  if (
    typeof input.role_id === "number" &&
    input.role_id > 0 &&
    input.role_id !== createdUser.role_id
  ) {
    return updateUser(session, createdUser.id, { role_id: input.role_id });
  }

  return createdUser;
}

export async function updateUser(
  session: UserSession,
  userId: number,
  input: UserUpdateInput,
): Promise<AdminUser> {
  return requestJson<AdminUser>(`/api/users/${userId}`, {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "PUT",
  });
}

export async function resetUserPassword(
  session: UserSession,
  userId: number,
  newPassword: string,
): Promise<void> {
  await requestJson(`/api/users/${userId}/reset-password`, {
    body: JSON.stringify({ new_password: newPassword }),
    headers: jsonAuthHeaders(session),
    method: "POST",
  });
}

export async function deleteUser(
  session: UserSession,
  userId: number,
): Promise<void> {
  await requestJson(`/api/users/${userId}`, {
    headers: authHeaders(session),
    method: "DELETE",
  });
}

export async function listOrders(session: UserSession): Promise<AdminOrder[]> {
  return requestJson<AdminOrder[]>("/api/orders/", {
    headers: authHeaders(session),
    method: "GET",
  });
}

export async function updateOrderStatus(
  session: UserSession,
  orderId: number,
  input: OrderStatusUpdateInput,
): Promise<AdminOrder> {
  return requestJson<AdminOrder>(`/api/orders/${orderId}/status`, {
    body: JSON.stringify(input),
    headers: jsonAuthHeaders(session),
    method: "PUT",
  });
}

export async function deleteOrder(
  session: UserSession,
  orderId: number,
): Promise<void> {
  await requestJson(`/api/orders/${orderId}`, {
    headers: authHeaders(session),
    method: "DELETE",
  });
}

export async function listCarts(session: UserSession): Promise<AdminCart[]> {
  return requestJson<AdminCart[]>("/api/carts/", {
    headers: authHeaders(session),
    method: "GET",
  });
}

export async function clearCart(
  session: UserSession,
  cartId: number,
): Promise<void> {
  await requestJson(`/api/carts/${cartId}/clear`, {
    headers: authHeaders(session),
    method: "POST",
  });
}

export async function deleteCart(
  session: UserSession,
  cartId: number,
): Promise<void> {
  await requestJson(`/api/carts/${cartId}`, {
    headers: authHeaders(session),
    method: "DELETE",
  });
}
