"use client";
import { App, Avatar, Button } from "antd";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/utils/helper";
export default function Header() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const { message } = App.useApp();
  return <header className="topbar">
    <span className="topbar-label">Không gian giảng viên</span>
    <div className="header-actions">
      <Avatar style={{ background: "#256d62" }}>{user?.name?.charAt(0)}</Avatar>
      <span className="account-name">{user?.name}</span>
      <Button onClick={async () => {
        try { await signOut(); router.replace("/login"); }
        catch (error) { message.error(getErrorMessage(error)); }
      }}>Đăng xuất</Button>
    </div>
  </header>;
}

