"use client";
import Link from "next/link";
import { Button, Card, Progress, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { useAuth } from "@/hooks/useAuth";

const quickSteps = [
  ["📚", "Tạo khóa học", "Đặt tên khóa học và chọn bài giảng sẽ dùng trong buổi dạy."],
  ["📤", "Tải lên bài giảng", "Mockup nhận file PPTX/PDF và giả lập bước phân tích nội dung."],
  ["🧠", "Soạn checkpoint", "AI hỗ trợ tạo câu hỏi trắc nghiệm để giảng viên duyệt trước."],
  ["🎙️", "Vào Bục Giảng", "Tạo phòng học 5 ký tự, trình chiếu và mở câu hỏi cho học viên."],
];

export default function DashboardPage() {
  const { user } = useAuth();
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">KHÔNG GIAN GIẢNG VIÊN</p>
      <h1>Chào {user?.name || "giảng viên"}! 👋</h1>
      <p className="muted">Chuẩn bị bài giảng, tạo lớp học và theo dõi nhịp hiểu của lớp trong lúc dạy.</p>
    </div><Tag color="green">🌱 Growup · Mockup Flow</Tag></div>

    <Card className="welcome-card"><div className="welcome-content">
      <div><p className="eyebrow">BẮT ĐẦU BUỔI DẠY MỚI</p><h2>Tạo khóa học và vào Bục Giảng</h2>
        <p>Tải lên bài giảng mockup, để AI hỗ trợ soạn checkpoint, rồi tạo phòng học 5 ký tự cho học viên vào theo dõi.</p></div>
      <div className="dashboard-actions"><Link href="/lessons/new"><Button type="primary" size="large">Tạo khóa học</Button></Link>
        <Link href="/join"><Button size="large">Xem lối vào học viên</Button></Link></div>
    </div></Card>

    <div className="dashboard-grid four-steps">{quickSteps.map(([icon, title, text], index) =>
      <Card key={title} className="dashboard-step-card">
        <div className="dashboard-step-top"><span className="step-bubble">{icon}</span><b>0{index + 1}</b></div>
        <h3>{title}</h3><p className="muted">{text}</p>
      </Card>)}</div>

    <div className="dashboard-two-column">
      <Card title="Khóa học gần đây" className="recent-lesson-card">
        <div className="empty-lessons"><span>🎙️</span><h3>Chưa có khóa học mockup nào</h3>
          <p>Tạo khóa học đầu tiên để mở Bục Giảng và mời học viên bằng mã phòng.</p><Link href="/lessons/new"><Button type="primary">Tạo khóa học đầu tiên</Button></Link></div>
      </Card>
      <Card title="Mục tiêu thiết lập">
        <div className="setup-progress"><Progress percent={25} strokeColor="#58cc02" />
          <p><strong>1/4 bước hoàn thành</strong></p>
          <ul><li className="done">✓ Tạo tài khoản giảng viên</li><li>○ Tạo khóa học</li><li>○ Tải lên bài giảng</li><li>○ Vào Bục Giảng</li></ul>
        </div>
      </Card>
    </div>
  </AppLayout>;
}
