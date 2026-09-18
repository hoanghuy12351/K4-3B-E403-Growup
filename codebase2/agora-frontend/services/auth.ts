import { apiRequest, USE_MOCK } from "./api";
import type { AuthSession, LoginInput } from "@/types/user";

export async function login(input: LoginInput): Promise<AuthSession> {
  if (!USE_MOCK) return apiRequest<AuthSession>("/auth/login", {
    method: "POST", body: JSON.stringify(input),
  });
  const email = input.email.trim().toLowerCase();
  return { user: { id: "demo-teacher", name: "Giảng viên dùng thử", email, role: "teacher" } };
}
export async function getSession(): Promise<AuthSession> {
  return apiRequest<AuthSession>("/auth/me");
}
export async function logout(): Promise<void> {
  if (!USE_MOCK) await apiRequest<void>("/auth/logout", { method: "POST" });
}

