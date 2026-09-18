"use client";

import Link from "next/link";
import { Button } from "antd";
import { useAuth } from "@/hooks/useAuth";

export default function PublicHeader() {
  const { user, ready } = useAuth();
  return <header className="public-header">
    <Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link>
    <nav aria-label="Điều hướng trang giới thiệu">
      <a href="#cach-hoat-dong">Cách hoạt động</a>
      <a href="#an-toan">Nguyên tắc</a>
    </nav>
    <div className="public-actions">
      <Link href="/join"><Button>Học viên vào lớp</Button></Link>
      {ready && user
        ? <Link href="/dashboard"><Button type="primary">Mở không gian giảng viên</Button></Link>
        : <Link href="/login"><Button type="primary">Đăng nhập giảng viên</Button></Link>}
    </div>
  </header>;
}
