"use client";

import Link from "next/link";
import { useState } from "react";
import { Alert, Button, Card, Form, Input, Tag } from "antd";
import type { StudentJoinInput } from "@/types/user";
import { joinRoom, type RoomJoinResult } from "@/services/diagnostic";

export default function JoinPage() {
  const [joined, setJoined] = useState<(StudentJoinInput & RoomJoinResult) | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (joined) return <main className="join-page"><section className="join-shell">
    <Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link>
    <Card className="join-success"><Tag color="green">Đã vào lượt kiểm tra</Tag>
      <h1>Chào {joined.displayName}</h1>
      <p>Giảng viên đang chuẩn bị mở checkpoint cho mã <strong>{joined.roomCode}</strong>.</p>
      <Alert type="info" showIcon title="Bạn không cần tài khoản"
        description="Tên hiển thị chỉ dùng trong lượt kiểm tra này để giảng viên xem phản hồi." />
      <div className="student-flow"><span>1 · Đọc câu hỏi</span><span>2 · Chọn đáp án</span><span>3 · Giải thích ngắn</span></div>
      <Button onClick={() => setJoined(null)}>Đổi mã hoặc tên</Button>
    </Card>
  </section></main>;

  return <main className="join-page"><section className="join-shell">
    <Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link>
    <div className="join-copy"><p className="eyebrow">DÀNH CHO HỌC VIÊN</p>
      <h1>Vào lượt kiểm tra</h1><p>Nhập mã giảng viên cung cấp và tên hiển thị. Bạn không cần đăng ký hoặc đăng nhập.</p></div>
    <Card className="join-card">
      {error && <Alert type="error" showIcon title="Không thể vào lớp" description={error} />}
      <Form<StudentJoinInput> layout="vertical" requiredMark={false}
        onFinish={async values => {
          setError(null);
          const sessionCode = values.sessionCode.trim().toUpperCase();
          const displayName = values.displayName.trim();
          try {
            const result = await joinRoom(sessionCode, displayName);
            sessionStorage.setItem("growup-participant", JSON.stringify(result));
            setJoined({ sessionCode, displayName, ...result });
          } catch (joinError) {
            setError(joinError instanceof Error ? joinError.message : "Vui lòng kiểm tra mã phòng và thử lại.");
          }
        }}>
        <Form.Item name="sessionCode" label="Mã lượt kiểm tra" normalize={value => String(value).toUpperCase()}
          rules={[{ required: true, whitespace: true, message: "Nhập mã lượt kiểm tra." },
            { pattern: /^[A-Z0-9-]{4,12}$/i, message: "Mã gồm 4–12 chữ, số hoặc dấu gạch ngang." }]}>
          <Input size="large" maxLength={12} placeholder="Ví dụ: VL-A2" autoComplete="off" />
        </Form.Item>
        <Form.Item name="displayName" label="Tên hiển thị" extra="Giảng viên sẽ thấy tên này cùng câu trả lời của bạn."
          rules={[{ required: true, whitespace: true, message: "Nhập tên hiển thị." },
            { min: 2, max: 50, message: "Tên cần từ 2 đến 50 ký tự." }]}>
          <Input size="large" maxLength={50} placeholder="Ví dụ: Minh Anh" autoComplete="off" />
        </Form.Item>
        <Button size="large" type="primary" htmlType="submit" block>Vào lượt kiểm tra</Button>
      </Form>
      <p className="join-privacy">Growup không yêu cầu email hoặc mật khẩu của học viên.</p>
    </Card>
    <Link className="back-link" href="/">← Quay lại trang giới thiệu</Link>
  </section></main>;
}
