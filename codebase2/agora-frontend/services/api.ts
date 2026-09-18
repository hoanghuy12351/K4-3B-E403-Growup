export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(API_URL + path, {
    ...options, headers, credentials: "include", cache: "no-store",
    signal: options.signal ?? AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail = payload && typeof payload === "object" && "detail" in payload
      ? payload.detail : null;
    throw new Error(typeof detail === "string" ? detail : `Yêu cầu thất bại (mã ${response.status}).`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

