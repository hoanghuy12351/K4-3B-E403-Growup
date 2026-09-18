"use client";

import { useEffect, useState } from "react";
import { Alert, Button, Card, Form, InputNumber, List, Select, Space, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { createDiagnosticSession, listLessonMaterials, startDiagnosticSession, type AvailableLessonMaterial, type CreatedSession } from "@/services/diagnostic";

type LessonForm = { materialId: string; expectedStudents?: number };

export default function NewDiagnosticPage() {
  const [form] = Form.useForm<LessonForm>();
  const [session, setSession] = useState<CreatedSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [materials, setMaterials] = useState<AvailableLessonMaterial[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);

  useEffect(() => {
    let active = true;
    listLessonMaterials().then((result) => {
      if (active) setMaterials(result.materials);
    }).catch((caught: unknown) => {
      if (active) setError(caught instanceof Error ? caught.message : "Không thể tải danh sách bài giảng.");
    }).finally(() => {
      if (active) setLoadingMaterials(false);
    });
    return () => { active = false; };
  }, []);

  async function generate(values: LessonForm) {
    setLoading(true);
    setError(null);
    try {
      setSession(await createDiagnosticSession({ lesson: { materialId: values.materialId }, expectedStudents: values.expectedStudents }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Không thể tạo phiên kiểm tra.");
    } finally {
      setLoading(false);
    }
  }

  async function start() {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      await startDiagnosticSession(session.sessionId);
      setSession({ ...session, status: "active" });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Không thể bắt đầu phiên kiểm tra.");
    } finally {
      setLoading(false);
    }
  }

  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">DIAGNOSTIC SESSION</p><h1>Tạo kiểm tra theo từng phần bài học</h1><p className="muted">Hệ thống tạo một câu hỏi cho mỗi section. Giảng viên xem trước rồi mới mở cho học viên.</p></div></div>
    {error && <Alert className="diagnostic-alert" type="error" showIcon title={error} />}
    {!session && <Card title="Chọn bài giảng"><p className="muted">Danh sách được đọc tự động từ thư mục backend <code>data/</code>. Hệ thống ánh xạ PDF đã chọn sang nội dung bài học mock ổn định, chia section và gửi từng section sang AI.</p><Form form={form} layout="vertical" onFinish={generate} initialValues={{ expectedStudents: 30 }}>
      <Form.Item label="Bài giảng hoặc PDF" name="materialId" rules={[{ required: true, message: "Chọn một bài giảng." }]}>{loadingMaterials ? <Spin /> : <Select placeholder="Chọn PDF từ data/" options={materials.map((material) => ({ value: material.id, label: material.title }))} />}</Form.Item>
      <Form.Item label="Số học viên dự kiến" name="expectedStudents"><InputNumber min={1} max={10000} /></Form.Item>
      <Button type="primary" htmlType="submit" loading={loading} disabled={loadingMaterials || !materials.length}>Tạo diagnostic</Button>
    </Form></Card>}
    {session && <Space direction="vertical" size="large" className="diagnostic-stack">
      <Alert type="success" showIcon title={`Đã tạo ${session.sections.length} section ở trạng thái draft.`} description="Hãy kiểm tra câu hỏi trước khi mở phiên cho học viên." />
      <List dataSource={session.sections} renderItem={(item) => <Card key={item.sectionId} title={<Space><Tag color="green">Phần {item.section.order}</Tag><span>{item.section.title}</span></Space>}>
        <p className="muted">Khái niệm: {item.concepts.join(", ") || "Chưa xác định"}</p>
        <h3>{item.question.question}</h3>
        <List size="small" dataSource={item.question.options} renderItem={(option) => <List.Item><Tag color={option.correct ? "green" : "default"}>{option.id}</Tag>{option.text}</List.Item>} />
      </Card>} />
      {session.status === "draft" ? <Button type="primary" onClick={start} loading={loading}>Mở phiên cho học viên</Button> : <Card title="Mở hai tab riêng biệt">
        <p className="muted">Gửi liên kết tab Học viên cho lớp. Giữ tab Báo cáo giảng viên riêng để theo dõi phản hồi.</p>
        <Space wrap><Button type="primary" href={`/diagnostic/${session.sessionId}/student`} target="_blank" rel="noreferrer">Mở tab học viên</Button><Button href={`/diagnostic/${session.sessionId}/report`} target="_blank" rel="noreferrer">Mở tab báo cáo giảng viên</Button></Space>
      </Card>}
    </Space>}
  </AppLayout>;
}
