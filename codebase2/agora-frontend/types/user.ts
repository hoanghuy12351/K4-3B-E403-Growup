export type UserRole = "teacher" | "student";
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}
export type UserInput = Omit<User, "id">;
export interface LoginInput { email: string; password: string }
export interface AuthSession { user: User }

