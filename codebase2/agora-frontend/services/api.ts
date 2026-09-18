export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export interface ApiRequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { timeoutMs = 15000, ...requestOptions } = options;
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(API_URL + path, {
    ...requestOptions, headers, credentials: "include", cache: "no-store",
    signal: options.signal ?? AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail = payload && typeof payload === "object" && "detail" in payload
      ? payload.detail : null;
    const nestedError = detail && typeof detail === "object" && "error" in detail ? detail.error : null;
    const message = nestedError && typeof nestedError === "object" && "message" in nestedError
      ? nestedError.message : detail;
    const errorCode = nestedError && typeof nestedError === "object" && "code" in nestedError && typeof nestedError.code === "string"
      ? nestedError.code : "";
    const friendlyMessage = response.status === 401 ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
      : errorCode === "AI_PROVIDER_CONFIGURATION_ERROR" ? "Teaching Agent chưa được cấu hình API key/model hợp lệ."
      : errorCode === "AI_PROVIDER_TIMEOUT" ? "AI mất quá lâu để tạo checkpoint. Hãy thử lại."
      : errorCode === "AI_OUTPUT_INVALID" ? "AI trả về câu hỏi chưa đúng định dạng. Hãy tạo lại."
      : errorCode === "DEMO_SECTION_NOT_FOUND" ? "Phần bài giảng này không tồn tại trong demo."
      : typeof message === "string" ? message : `Yêu cầu thất bại (mã ${response.status}).`;
    throw new Error(friendlyMessage);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

