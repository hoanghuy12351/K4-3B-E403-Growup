import { apiRequest, USE_MOCK } from "./api";
import type { User, UserInput } from "@/types/user";
const KEY = "growup-demo-users-v1";
const SAMPLE: User[] = [
  { id: "demo-1", name: "Giảng viên mẫu", email: "teacher@example.com", role: "teacher" },
  { id: "demo-2", name: "Học viên mẫu 01", email: "student01@example.com", role: "student" },
  { id: "demo-3", name: "Học viên mẫu 02", email: "student02@example.com", role: "student" },
];
function readUsers(): User[] {
  const raw = localStorage.getItem(KEY);
  if (!raw) return SAMPLE.map(user => ({ ...user }));
  try { return JSON.parse(raw) as User[]; }
  catch { throw new Error("Dữ liệu dùng thử không đọc được. Hãy xóa dữ liệu trang trong trình duyệt."); }
}
function saveUsers(users: User[]) { localStorage.setItem(KEY, JSON.stringify(users)); }
function normalize(input: UserInput): UserInput {
  return { ...input, name: input.name.trim(), email: input.email.trim().toLowerCase() };
}
function assertUnique(users: User[], email: string, id?: string) {
  if (users.some(user => user.id !== id && user.email.toLowerCase() === email)) {
    throw new Error("Email này đã được sử dụng.");
  }
}
export async function getUsers(): Promise<User[]> {
  return USE_MOCK ? readUsers() : apiRequest<User[]>("/users");
}
export async function createUser(input: UserInput): Promise<User> {
  const data = normalize(input);
  if (!USE_MOCK) return apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });
  const users = readUsers();
  assertUnique(users, data.email);
  const user = { ...data, id: crypto.randomUUID() };
  saveUsers([...users, user]);
  return user;
}
export async function updateUser(id: string, input: UserInput): Promise<User> {
  const data = normalize(input);
  if (!USE_MOCK) return apiRequest<User>("/users/" + encodeURIComponent(id), {
    method: "PUT", body: JSON.stringify(data),
  });
  const users = readUsers();
  if (!users.some(user => user.id === id)) throw new Error("Người dùng không còn tồn tại.");
  assertUnique(users, data.email, id);
  const user = { ...data, id };
  saveUsers(users.map(item => item.id === id ? user : item));
  return user;
}
export async function deleteUser(id: string): Promise<void> {
  if (!USE_MOCK) return apiRequest<void>("/users/" + encodeURIComponent(id), { method: "DELETE" });
  saveUsers(readUsers().filter(user => user.id !== id));
}

