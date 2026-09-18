export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function apiRequest<T>(path: string, options: RequestInit = {}, timeoutMs = 15000): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(API_URL + path, {
    ...options, headers, credentials: "include", cache: "no-store",
    signal: options.signal ?? AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const record = payload && typeof payload === "object" ? payload as Record<string, unknown> : null;
    const detail = record?.detail;
    const error = record?.error ?? (detail && typeof detail === "object" ? (detail as Record<string, unknown>).error : null);
    const message = error && typeof error === "object" ? (error as Record<string, unknown>).message : null;
    throw new Error(typeof message === "string" ? message : typeof detail === "string" ? detail : `Yêu cầu thất bại (mã ${response.status}).`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

