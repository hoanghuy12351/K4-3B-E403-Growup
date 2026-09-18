import { apiRequest, USE_MOCK } from "./api";
import type { AuthSession, LoginInput, RegisterInput, Teacher } from "@/types/user";

interface StoredTeacher extends Teacher {
  passwordHash: string;
  passwordSalt: string;
}

const ACCOUNT_KEY = "growup-demo-teachers-v2";
const encoder = new TextEncoder();

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach(byte => { binary += String.fromCharCode(byte); });
  return btoa(binary);
}

function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value);
  return Uint8Array.from(binary, char => char.charCodeAt(0));
}

async function hashPassword(password: string, salt: Uint8Array): Promise<string> {
  const material = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({
    name: "PBKDF2", salt: salt as BufferSource, iterations: 120_000, hash: "SHA-256",
  }, material, 256);
  return bytesToBase64(new Uint8Array(bits));
}

function readAccounts(): StoredTeacher[] {
  const raw = localStorage.getItem(ACCOUNT_KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as StoredTeacher[]; }
  catch { throw new Error("Dữ liệu tài khoản dùng thử bị lỗi. Hãy xóa dữ liệu trang và thử lại."); }
}

function writeAccounts(accounts: StoredTeacher[]): void {
  localStorage.setItem(ACCOUNT_KEY, JSON.stringify(accounts));
}

async function ensureDemoAccount(): Promise<StoredTeacher[]> {
  const accounts = readAccounts();
  if (accounts.length) return accounts;
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const demo: StoredTeacher = {
    id: "demo-teacher",
    name: "Giảng viên dùng thử",
    email: "teacher@example.com",
    role: "teacher",
    passwordSalt: bytesToBase64(salt),
    passwordHash: await hashPassword("demo123456", salt),
  };
  writeAccounts([demo]);
  return [demo];
}

function publicTeacher(account: StoredTeacher): Teacher {
  const { id, name, email, role } = account;
  return { id, name, email, role };
}

export async function login(input: LoginInput): Promise<AuthSession> {
  if (!USE_MOCK) return apiRequest<AuthSession>("/auth/login", {
    method: "POST", body: JSON.stringify(input),
  });
  const email = input.email.trim().toLowerCase();
  const account = (await ensureDemoAccount()).find(item => item.email === email);
  if (!account) throw new Error("Email hoặc mật khẩu chưa đúng.");
  const passwordHash = await hashPassword(input.password, base64ToBytes(account.passwordSalt));
  if (passwordHash !== account.passwordHash) throw new Error("Email hoặc mật khẩu chưa đúng.");
  return { user: publicTeacher(account) };
}

export async function register(input: RegisterInput): Promise<AuthSession> {
  if (!USE_MOCK) return apiRequest<AuthSession>("/auth/register", {
    method: "POST", body: JSON.stringify({ name: input.name, email: input.email, password: input.password }),
  });
  const accounts = await ensureDemoAccount();
  const email = input.email.trim().toLowerCase();
  if (accounts.some(account => account.email === email)) throw new Error("Email này đã có tài khoản giảng viên.");
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const account: StoredTeacher = {
    id: crypto.randomUUID(), name: input.name.trim(), email, role: "teacher",
    passwordSalt: bytesToBase64(salt),
    passwordHash: await hashPassword(input.password, salt),
  };
  writeAccounts([...accounts, account]);
  return { user: publicTeacher(account) };
}

export async function getSession(): Promise<AuthSession> {
  return apiRequest<AuthSession>("/auth/me", { timeoutMs: 3000 });
}

export async function logout(): Promise<void> {
  if (!USE_MOCK) await apiRequest<void>("/auth/logout", { method: "POST" });
}
