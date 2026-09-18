"use client";
import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "antd";
import { useAuth } from "@/hooks/useAuth";
import { USE_MOCK } from "@/services/api";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Loading from "@/components/Loading";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();
  useEffect(() => { if (ready && !user) router.replace("/login"); }, [ready, user, router]);
  if (!ready || !user) return <Loading />;
  return <div className="app-shell"><Sidebar /><div className="main-area">
    <Header /><main className="page-content">
      {USE_MOCK && <Alert className="demo-alert" type="info" showIcon
        title="Chế độ dùng thử · Dữ liệu mẫu, chưa kết nối VLearn hoặc cơ sở dữ liệu." />}
      {children}
    </main>
  </div></div>;
}

