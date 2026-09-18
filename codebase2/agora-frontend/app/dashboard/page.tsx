"use client";
import Link from "next/link";
import { Button, Card, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  const { user } = useAuth();
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">TỔNG QUAN</p>
      <h1>Xin chào, {user?.name || "giảng viên"}</h1>
      <p className="muted">Chuẩn bị một nhịp kiểm tra trước khi chuyển phần bài học.</p>
    </div><Tag color="green">Growup · A2</Tag></div>
    <Card className="welcome-card"><div className="welcome-content">
      <div><p className="eyebrow">KIỂM TRA MỨC HIỂU</p><h2>Lớp đang theo kịp ở đâu?</h2>
      <p>Thu câu trả lời ngắn, xem hiểu lầm theo khái niệm và quyết định cách dạy tiếp.</p></div>
      <Link href="/users"><Button type="primary" size="large">Quản lý người dùng</Button></Link>
    </div></Card>
    <div className="dashboard-grid">
      {[
        ["01", "Chọn khái niệm", "Xác định nội dung cần kiểm tra sau một phần bài học."],
        ["02", "Thu phản hồi", "Học viên trả lời câu hỏi và giải thích ngắn."],
        ["03", "Xem bằng chứng", "Giảng viên xem kết quả rồi chọn giảng lại hoặc tiếp tục."],
      ].map(([number, title, text]) => <Card key={number}><span className="step-number">{number}</span>
        <h3>{title}</h3><p className="muted">{text}</p></Card>)}
    </div>
    <Card title="Không gian làm việc"><p>Trang người dùng đã có chức năng thêm, sửa và xóa để dùng thử.</p>
      <p className="muted">Luồng kiểm tra mức hiểu sẽ được bổ sung ở bước triển khai tiếp theo.</p>
    </Card>
  </AppLayout>;
}

