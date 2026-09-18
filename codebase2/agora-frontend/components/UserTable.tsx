"use client";
import { Button, Popconfirm, Space, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { User } from "@/types/user";
import { roleLabel } from "@/utils/helper";

interface Props {
  users: User[]; loading: boolean; deleting: string | null;
  onEdit: (user: User) => void; onDelete: (id: string) => Promise<void>;
}
export default function UserTable({ users, loading, deleting, onEdit, onDelete }: Props) {
  const columns: ColumnsType<User> = [
    { title: "Họ tên", dataIndex: "name" },
    { title: "Email", dataIndex: "email" },
    { title: "Vai trò", dataIndex: "role", render: role =>
      <Tag color={role === "teacher" ? "green" : "blue"}>{roleLabel(role)}</Tag> },
    { title: "Thao tác", key: "actions", render: (_, user) => <Space>
      <Button size="small" onClick={() => onEdit(user)}>Sửa</Button>
      <Popconfirm title="Xóa người dùng này?" description="Thông tin người dùng sẽ bị xóa."
        okText="Xóa" cancelText="Hủy" onConfirm={() => onDelete(user.id)}>
        <Button size="small" danger disabled={deleting !== null} loading={deleting === user.id}>Xóa</Button>
      </Popconfirm>
    </Space> },
  ];
  return <Table<User> rowKey="id" columns={columns} dataSource={users} loading={loading}
    scroll={{ x: 650 }} pagination={{ pageSize: 8, hideOnSinglePage: true }}
    locale={{ emptyText: "Chưa có người dùng." }} />;
}

