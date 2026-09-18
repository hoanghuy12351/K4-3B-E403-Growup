"use client";
import { useEffect, useState, type ReactNode } from "react";
import { App, ConfigProvider } from "antd";
import viVN from "antd/locale/vi_VN";
import { AuthStoreContext, createAuthStore, DEMO_SESSION_KEY } from "@/stores/authStore";
import { USE_MOCK } from "@/services/api";
import { getSession } from "@/services/auth";
import type { Teacher } from "@/types/user";

export default function Providers({ children }: { children: ReactNode }) {
  const [store] = useState(createAuthStore);
  useEffect(() => {
    let active = true;
    async function restore() {
      try {
        if (USE_MOCK) {
          const raw = localStorage.getItem(DEMO_SESSION_KEY);
          if (raw && active) {
            const user = JSON.parse(raw) as Teacher;
            if (typeof user.id === "string" && typeof user.name === "string" && typeof user.email === "string"
              && user.role === "teacher") store.getState().setUser(user);
          }
        } else {
          const session = await getSession();
          if (active) store.getState().setUser(session.user);
        }
      } catch {
        // Không có phiên hợp lệ: chuyển về đăng nhập.
        if (active) store.getState().setUser(null);
      } finally {
        store.getState().setReady();
      }
    }
    void restore();
    return () => { active = false; };
  }, [store]);
  return <AuthStoreContext.Provider value={store}>
    <ConfigProvider locale={viVN} theme={{ token: {
      colorPrimary: "#58cc02", colorInfo: "#1cb0f6", colorSuccess: "#58cc02",
      colorWarning: "#ffc800", colorError: "#ff4b4b", borderRadius: 16,
      fontFamily: "Nunito, Arial, sans-serif", controlHeightLG: 50,
    } }}>
      <App>{children}</App>
    </ConfigProvider>
  </AuthStoreContext.Provider>;
}

