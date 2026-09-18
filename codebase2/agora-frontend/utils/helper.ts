export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Đã xảy ra lỗi. Vui lòng thử lại.";
}
export function roleLabel(role: "teacher" | "student"): string {
  return role === "teacher" ? "Giảng viên" : "Học viên";
}

