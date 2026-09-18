"use client";
import Link from "next/link";
import { Button, Card, Progress, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { useAuth } from "@/hooks/useAuth";

const quickSteps = [
  ["📤", "Tải PPTX", "Đưa bài giảng lên để AI đọc nội dung và ghi chú."],
  ["🧠", "Duyệt checkpoint", "Xem các phần lớn, khái niệm trọng tâm và câu hỏi AI đề xuất."],
  ["🚀", "Mở lớp", "Chia sẻ mã phòng rồi kiểm tra mức hiểu ngay trong lúc dạy."],
];

export default function DashboardPage() {
  const { user } = useAuth();
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">KHÔNG GIAN GIẢNG VIÊN</p>
      <h1>Chào {user?.name || "giảng viên"}! 👋</h1>
      <p className="muted">Hôm nay bạn muốn lớp hiểu chắc phần nào?</p>
    </div><Tag color="green">🌱 Growup · AI hỗ trợ</Tag></div>

    <Card className="welcome-card"><div className="welcome-content">
      <div><p className="eyebrow">BẮT ĐẦU BÀI GIẢNG MỚI</p><h2>Biến slide thành checkpoint thông minh</h2>
        <p>Tải file PPTX lên. AI sẽ chia các phần kiến thức lớn, chọn ba ý trọng tâm và soạn câu hỏi để bạn duyệt.</p></div>
      <div className="dashboard-actions"><Button type="primary" size="large">📤 Tải PPTX lên</Button>
        <Link href="/join"><Button size="large">Xem lối vào học viên</Button></Link></div>
    </div></Card>

    <div className="dashboard-grid">{quickSteps.map(([icon, title, text], index) =>
      <Card key={title} className="dashboard-step-card">
        <div className="dashboard-step-top"><span className="step-bubble">{icon}</span><b>0{index + 1}</b></div>
        <h3>{title}</h3><p className="muted">{text}</p>
      </Card>)}</div>

    <div className="dashboard-two-column">
      <Card title="Bài giảng gần đây" className="recent-lesson-card">
        <div className="empty-lessons"><span>📚</span><h3>Chưa có bài giảng nào</h3>
          <p>Tải file đầu tiên để AI bắt đầu phân tích nội dung.</p><Button type="primary">Tải bài giảng đầu tiên</Button></div>
      </Card>
      <Card title="Mục tiêu thiết lập">
        <div className="setup-progress"><Progress percent={25} strokeColor="#58cc02" />
          <p><strong>1/4 bước hoàn thành</strong></p>
          <ul><li className="done">✓ Tạo tài khoản giảng viên</li><li>○ Tải bài giảng PPTX</li><li>○ Duyệt checkpoint đầu tiên</li><li>○ Mở phòng học</li></ul>
        </div>
      </Card>
    </div>
  </AppLayout>;
}

