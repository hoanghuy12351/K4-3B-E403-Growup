"use client";
import { useContext } from "react";
import { useStore } from "zustand";
import { AuthStoreContext, DEMO_SESSION_KEY } from "@/stores/authStore";
import * as authService from "@/services/auth";
import { USE_MOCK } from "@/services/api";
import type { LoginInput, RegisterInput } from "@/types/user";

export function useAuth() {
  const store = useContext(AuthStoreContext);
  if (!store) throw new Error("useAuth phải nằm trong Providers.");
  const state = useStore(store);
  return {
    user: state.user, ready: state.ready,
    async signIn(input: LoginInput) {
      const session = await authService.login(input);
      if (USE_MOCK) localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session.user));
      state.setUser(session.user);
    },
    async signUp(input: RegisterInput) {
      const session = await authService.register(input);
      if (USE_MOCK) localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session.user));
      state.setUser(session.user);
    },
    async signOut() {
      await authService.logout();
      localStorage.removeItem(DEMO_SESSION_KEY);
      state.setUser(null);
    },
  };
}
