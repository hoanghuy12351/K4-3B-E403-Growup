"use client";

import Link from "next/link";
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
  const [form] = Form.useForm<LoginInput>();
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (ready && user) router.replace("/dashboard");
  }, [ready, user, router]);

  if (ready && user) return <Loading />;

  return (
    <main className="login-page auth-playground">
      <section className="login-story">
        <Link className="brand" href="/">
          <span className="brand-mark">G</span>Growup
        </Link>
        <p className="eyebrow">ĐĂNG NHẬP GIẢNG VIÊN</p>
        <h1>
          Hiểu lớp hơn.
          <br />
          Dạy tiếp vững hơn.
        </h1>
        <p>
          Một nơi để chuẩn bị kiểm tra, xem phản hồi và chọn cách hỗ trợ học
          viên ngay trong buổi học.
        </p>
        <div className="story-badges">
          <span>🙋 Học viên không cần tài khoản</span>
        </div>
        <span className="story-footer">
          Chỉ giảng viên cần đăng nhập để quản lý buổi học.
        </span>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <Link className="back-link" href="/">
            ← Trang giới thiệu
          </Link>
          <h2>Chào mừng trở lại</h2>
          <p className="muted">Đăng nhập tài khoản giảng viên.</p>
          <Alert
            type="info"
            title="Tài khoản giảng viên mẫu"
            description="Email: teacher@example.com · Mật khẩu: demo123456"
            showIcon
            style={{ marginBottom: 20 }}
          />
          {formError && (
            <Alert
              type="error"
              title="Đăng nhập không thành công"
              description={formError}
              showIcon
              closable
              onClose={() => setFormError(null)}
              style={{ marginBottom: 20 }}
            />
          )}
          <Form<LoginInput>
            form={form}
            layout="vertical"
            requiredMark={false}
            initialValues={{
              email: "teacher@example.com",
              password: "demo123456",
            }}
            onSubmitCapture={(e) => {
              e.preventDefault();
            }}
            onFinish={async (values) => {
              setFormError(null);
              setSubmitting(true);
              try {
                console.log("[Login] Bắt đầu đăng nhập:", values.email);
                await signIn(values);
                console.log("[Login] Thành công, đang chuyển sang bục giảng...");
                message.success("Đăng nhập thành công! Đang chuyển hướng...");
                router.replace("/dashboard");
                setTimeout(() => {
                  window.location.assign("/dashboard");
                }, 400);
              } catch (error) {
                console.error("[Login] Lỗi:", error);
                const errorMsg = getErrorMessage(error);
                setFormError(errorMsg);
                message.error(errorMsg);
              } finally {
                setSubmitting(false);
              }
            }}
            onFinishFailed={(err) => {
              console.warn("[Login] Validation failed:", err);
              const firstErr = err.errorFields?.[0]?.errors?.[0];
              const msg = firstErr || "Vui lòng nhập đầy đủ email và mật khẩu (tối thiểu 8 ký tự).";
              setFormError(msg);
              message.warning(msg);
            }}
          >
            <Form.Item
              name="email"
              label="Email"
              rules={[
                { required: true, message: "Nhập email." },
                { type: "email", message: "Email chưa hợp lệ." },
              ]}
            >
              <Input
                size="large"
                autoComplete="username"
                placeholder="teacher@example.com"
              />
            </Form.Item>
            <Form.Item
              name="password"
              label="Mật khẩu"
              rules={[
                { required: true, message: "Nhập mật khẩu." },
                { min: 8, message: "Nhập ít nhất 8 ký tự." },
              ]}
            >
              <Input.Password
                size="large"
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </Form.Item>
            <Button
              size="large"
              type="primary"
              htmlType="button"
              block
              loading={submitting}
              onClick={() => {
                form.submit();
              }}
            >
              Đăng nhập
            </Button>
          </Form>
          <p className="form-switch">
            Chưa có tài khoản? <Link href="/register">Đăng ký giảng viên</Link>
          </p>
          <p className="student-shortcut">
            Bạn là học viên?{" "}
            <Link href="/join">Nhập mã, không cần tài khoản</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
