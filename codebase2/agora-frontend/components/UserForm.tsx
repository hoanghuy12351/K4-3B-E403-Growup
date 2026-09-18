"use client";
import { Form, Input, Modal, Select } from "antd";
import { useEffect } from "react";
import type { User, UserInput } from "@/types/user";

interface Props {
  open: boolean; user: User | null; saving: boolean;
  onCancel: () => void; onSave: (input: UserInput) => Promise<void>;
}
export default function UserForm({ open, user, saving, onCancel, onSave }: Props) {
  const [form] = Form.useForm<UserInput>();
  useEffect(() => {
    if (open) { form.resetFields(); form.setFieldsValue(user ?? { role: "student" }); }
  }, [open, user, form]);
  return <Modal open={open} title={user ? "Sửa người dùng" : "Thêm người dùng"}
    onCancel={saving ? undefined : onCancel} closable={!saving} maskClosable={!saving}
    onOk={() => form.submit()} confirmLoading={saving} okText="Lưu" cancelText="Hủy">
    <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
      <Form.Item name="name" label="Họ tên" rules={[{ required: true, whitespace: true, message: "Nhập họ tên." }]}>
        <Input maxLength={100} />
      </Form.Item>
      <Form.Item name="email" label="Email" rules={[{ required: true, message: "Nhập email." },
        { type: "email", message: "Email chưa hợp lệ." }]}><Input maxLength={254} /></Form.Item>
      <Form.Item name="role" label="Vai trò" rules={[{ required: true, message: "Chọn vai trò." }]}>
        <Select options={[{ value: "teacher", label: "Giảng viên" }, { value: "student", label: "Học viên" }]} />
      </Form.Item>
    </Form>
  </Modal>;
}

