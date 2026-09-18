"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, App, Button, Form, Input } from "antd";
import { useAuth } from "@/hooks/useAuth";
import { USE_MOCK } from "@/services/api";
import { getErrorMessage } from "@/utils/helper";
import Loading from "@/components/Loading";
import type { RegisterInput } from "@/types/user";

export default function RegisterPage() {
  const { user, ready, signUp } = useAuth();
  const router = useRouter();
  const { message } = App.useApp();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { if (ready && user) router.replace("/dashboard"); }, [ready, user, router]);
  if (!ready || user) return <Loading />;

  return <main className="login-page auth-playground">
    <section className="login-story register-story">
      <Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link>
      <p className="eyebrow">TÀI KHOẢN GIẢNG VIÊN</p>
      <h1>Tạo một nhịp<br />kiểm tra cho lớp.</h1>
      <p>Tài khoản dùng để chuẩn bị câu hỏi, mở lượt kiểm tra và xem tổng hợp mức hiểu của lớp.</p>
      <div className="story-badges"><span>📤 Tải slide</span><span>✨ AI đề xuất</span><span>✅ Bạn duyệt</span></div>
      <span className="story-footer">Học viên không cần đăng ký tài khoản.</span>
    </section>
    <section className="login-panel"><div className="login-card register-card">
      <Link className="back-link" href="/">← Trang giới thiệu</Link>
      <h2>Đăng ký giảng viên</h2><p className="muted">Chỉ giảng viên cần tài khoản Growup.</p>
      {USE_MOCK && <Alert type="info" title="Chế độ dùng thử"
        description="Tài khoản được lưu trên trình duyệt này. Không dùng mật khẩu thật."
        showIcon style={{ marginBottom: 24 }} />}
      <Form<RegisterInput> layout="vertical" requiredMark={false} onFinish={async values => {
        setSubmitting(true);
        try { await signUp(values); message.success("Đã tạo tài khoản giảng viên."); router.replace("/dashboard"); }
        catch (error) { message.error(getErrorMessage(error)); }
        finally { setSubmitting(false); }
      }}>
        <Form.Item name="name" label="Họ tên" rules={[{ required: true, whitespace: true, message: "Nhập họ tên." },
          { min: 2, message: "Tên cần ít nhất 2 ký tự." }]}><Input size="large" autoComplete="name" placeholder="Ví dụ: Võ Huy Hoàng" /></Form.Item>
        <Form.Item name="email" label="Email" rules={[{ required: true, message: "Nhập email." },
          { type: "email", message: "Email chưa hợp lệ." }]}><Input size="large" autoComplete="email" placeholder="teacher@example.com" /></Form.Item>
        <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, message: "Nhập mật khẩu." },
          { min: 8, message: "Nhập ít nhất 8 ký tự." }]}><Input.Password size="large" autoComplete="new-password" /></Form.Item>
        <Form.Item name="confirmPassword" label="Nhập lại mật khẩu" dependencies={["password"]}
          rules={[{ required: true, message: "Nhập lại mật khẩu." }, ({ getFieldValue }) => ({
            validator(_, value) { return !value || getFieldValue("password") === value
              ? Promise.resolve() : Promise.reject(new Error("Hai mật khẩu chưa trùng nhau.")); },
          })]}><Input.Password size="large" autoComplete="new-password" /></Form.Item>
        <Button size="large" type="primary" htmlType="submit" block loading={submitting}>Tạo tài khoản</Button>
      </Form>
      <p className="form-switch">Đã có tài khoản? <Link href="/login">Đăng nhập</Link></p>
      <p className="student-shortcut">Bạn là học viên? <Link href="/join">Nhập mã, không cần tài khoản</Link></p>
    </div></section>
  </main>;
}
