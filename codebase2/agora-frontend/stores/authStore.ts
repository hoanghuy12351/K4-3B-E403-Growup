"use client";
import { createContext } from "react";
import { createStore } from "zustand/vanilla";
import type { Teacher } from "@/types/user";

export interface AuthState {
  user: Teacher | null;
  ready: boolean;
  setUser: (user: Teacher | null) => void;
  setReady: () => void;
}
export function createAuthStore() {
  return createStore<AuthState>()(set => ({
    user: null, ready: false,
    setUser: user => set({ user }),
    setReady: () => set({ ready: true }),
  }));
}
export type AuthStore = ReturnType<typeof createAuthStore>;
export const AuthStoreContext = createContext<AuthStore | null>(null);
export const DEMO_SESSION_KEY = "growup-demo-session-v1";
