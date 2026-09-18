export interface Teacher {
  id: string;
  name: string;
  email: string;
  role: "teacher";
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput extends LoginInput {
  name: string;
  confirmPassword: string;
}

export interface AuthSession {
  user: Teacher;
}

export interface StudentJoinInput {
  sessionCode: string;
  displayName: string;
}

// Kiểu tương thích cho các thành phần quản trị cũ; tuyến /users hiện chuyển về dashboard.
export type UserRole = "teacher" | "student";
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}
export type UserInput = Omit<User, "id">;
