"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, App, Button, Form, Input } from "antd";
import { useAuth } from "@/hooks/useAuth";
import { USE_MOCK } from "@/services/api";
import { getErrorMessage } from "@/utils/helper";
import Loading from "@/components/Loading";
import type { LoginInput } from "@/types/user";

export default function LoginPage() {
  const { user, ready, signIn } = useAuth();
  const router = useRouter();
  const { message } = App.useApp();
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => { if (ready && user) router.replace("/dashboard"); }, [ready, user, router]);
  if (!ready || user) return <Loading />;
  return <main className="login-page">
    <section className="login-story">
      <span className="brand"><span className="brand-mark">G</span>Growup</span>
      <p className="eyebrow">KHÔNG GIAN GIẢNG VIÊN</p>
      <h1>Hiểu lớp hơn.<br />Dạy tiếp vững hơn.</h1>
      <p>Một nơi để chuẩn bị kiểm tra, xem phản hồi và chọn cách hỗ trợ học viên.</p>
      <span className="story-footer">VLearn · Nhóm Growup · A2</span>
    </section>
    <section className="login-panel"><div className="login-card">
      <h2>Chào mừng trở lại</h2><p className="muted">Đăng nhập để mở không gian làm việc.</p>
      {USE_MOCK && <Alert type="info" title="Đăng nhập mô phỏng"
        description="Dùng email bất kỳ hợp lệ và mật khẩu từ 6 ký tự. Không dùng mật khẩu thật."
        showIcon style={{ marginBottom: 24 }} />}
      <Form<LoginInput> layout="vertical" requiredMark={false}
        initialValues={USE_MOCK ? { email: "teacher@example.com" } : undefined}
        onFinish={async values => {
          setSubmitting(true);
          try { await signIn(values); router.replace("/dashboard"); }
          catch (error) { message.error(getErrorMessage(error)); }
          finally { setSubmitting(false); }
        }}>
        <Form.Item name="email" label="Email" rules={[{ required: true, message: "Nhập email." },
          { type: "email", message: "Email chưa hợp lệ." }]}>
          <Input size="large" autoComplete="username" placeholder="teacher@example.com" />
        </Form.Item>
        <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, message: "Nhập mật khẩu." },
          { min: 6, message: "Nhập ít nhất 6 ký tự." }]}>
          <Input.Password size="large" autoComplete="current-password" />
        </Form.Item>
        <Button size="large" type="primary" htmlType="submit" block loading={submitting}>Đăng nhập</Button>
      </Form>
    </div></section>
  </main>;
}

