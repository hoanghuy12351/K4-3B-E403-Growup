"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export default function Sidebar() {
  const pathname = usePathname();
  return <aside className="sidebar">
    <Link className="brand" href="/dashboard"><span className="brand-mark">G</span>Growup</Link>
    <div className="sidebar-caption">GIẢNG DẠY TRỰC TUYẾN</div>
    <nav aria-label="Điều hướng chính">
      {[["/dashboard", "Tổng quan"], ["/", "Trang giới thiệu"], ["/join", "Lối vào học viên"]].map(([href, label]) =>
        <Link key={href} href={href} className={pathname === href ? "nav-link active" : "nav-link"}
          aria-current={pathname === href ? "page" : undefined}>{label}</Link>)}
    </nav>
    <div className="sidebar-note">VLearn · Nhóm Growup<br />Kiểm tra hiểu trước khi dạy tiếp.</div>
  </aside>;
}
