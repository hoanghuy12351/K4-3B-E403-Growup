"use client";
import { useCallback, useEffect, useState } from "react";
import { Alert, App, Button, Card, Input } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import UserTable from "@/components/UserTable";
import UserForm from "@/components/UserForm";
import { useAuth } from "@/hooks/useAuth";
import * as service from "@/services/user";
import { getErrorMessage } from "@/utils/helper";
import type { User } from "@/types/user";

export default function UsersPage() {
  const { user: session, ready } = useAuth();
  const { message } = App.useApp();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setUsers(await service.getUsers()); }
    catch (err) { setError(getErrorMessage(err)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    if (!ready || !session) return;
    let active = true;
    void service.getUsers().then(items => {
      if (active) setUsers(items);
    }).catch(err => {
      if (active) setError(getErrorMessage(err));
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [ready, session]);
  const visible = users.filter(user => (user.name + " " + user.email).toLowerCase().includes(query.toLowerCase()));
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">QUẢN LÝ</p><h1>Người dùng</h1>
      <p className="muted">Danh sách giảng viên và học viên trong không gian làm việc.</p></div>
      <Button type="primary" size="large" onClick={() => { setEditing(null); setOpen(true); }}>Thêm người dùng</Button>
    </div>
    <Card>
      <div className="table-toolbar"><Input.Search aria-label="Tìm người dùng" placeholder="Tìm theo tên hoặc email"
        allowClear value={query} onChange={event => setQuery(event.target.value)} />
        <Button onClick={() => void load()} loading={loading}>Tải lại</Button></div>
      {error ? <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} /> : null}
      <UserTable users={visible} loading={loading} deleting={deleting}
        onEdit={user => { setEditing(user); setOpen(true); }}
        onDelete={async id => {
          setDeleting(id);
          try { await service.deleteUser(id); setUsers(items => items.filter(item => item.id !== id)); message.success("Đã xóa người dùng."); }
          catch (err) { message.error(getErrorMessage(err)); }
          finally { setDeleting(null); }
        }} />
    </Card>
    <UserForm open={open} user={editing} saving={saving} onCancel={() => setOpen(false)}
      onSave={async input => {
        setSaving(true);
        try {
          const result = editing ? await service.updateUser(editing.id, input) : await service.createUser(input);
          setUsers(items => editing ? items.map(item => item.id === result.id ? result : item) : [...items, result]);
          setOpen(false); message.success("Đã lưu người dùng.");
        } catch (err) { message.error(getErrorMessage(err)); }
        finally { setSaving(false); }
      }} />
  </AppLayout>;
}
