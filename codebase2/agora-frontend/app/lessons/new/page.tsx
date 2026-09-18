"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, InputNumber, Radio, Spin } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { createDiagnosticSession, listLessonMaterials, uploadLessonMaterial, type LessonMaterial } from "@/services/diagnostic";

export default function NewLessonPage() {
  const router = useRouter();
  const [materials, setMaterials] = useState<LessonMaterial[]>([]);
  const [selectedId, setSelectedId] = useState<string>();
  const [expectedStudents, setExpectedStudents] = useState(30);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listLessonMaterials()
      .then(items => { setMaterials(items); setSelectedId(items[0]?.id); })
      .catch(reason => setError(reason instanceof Error ? reason.message : "Không thể tải danh sách tài liệu."))
      .finally(() => setLoading(false));
  }, []);

  async function createSession(): Promise<void> {
    if (!selectedId) return;
    setError(null);
    setSubmitting(true);
    try {
      const session = await createDiagnosticSession(selectedId, expectedStudents);
      router.push(`/lessons/${session.sessionId}/checkpoints`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo checkpoint. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  async function upload(): Promise<void> {
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const material = await uploadLessonMaterial(file);
      setMaterials(current => [material, ...current]);
      setSelectedId(material.id);
      setFile(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu lên.");
    } finally {
      setUploading(false);
    }
  }

  return <AppLayout><div className="page-heading"><div><p className="eyebrow">BÀI GIẢNG MỚI</p><h1>Chọn tài liệu bài giảng</h1>
    <p className="muted">Tài liệu hiện dùng dữ liệu mẫu ổn định; chưa hỗ trợ tải PPTX trực tiếp.</p></div></div>
    <Card title="Tải tài liệu mới" className="recent-lesson-card" style={{ marginBottom: 16 }}>
      <p className="muted">Hỗ trợ PDF hoặc PPTX, tối đa 25 MB. Hệ thống chỉ trích xuất văn bản có trong tài liệu.</p>
      <input type="file" accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation" onChange={event => setFile(event.target.files?.[0] ?? null)} />
      <Button style={{ marginLeft: 12 }} loading={uploading} disabled={!file} onClick={upload}>Tải tài liệu lên</Button>
    </Card>
    <Card title="Tài liệu đã tải" className="recent-lesson-card">
      {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
      {loading ? <Spin tip="Đang tải tài liệu..." /> : <>
        {materials.length === 0 ? <Alert type="info" showIcon title="Chưa có tài liệu" description="Hãy thêm lesson material vào backend trước khi tạo checkpoint." /> :
          <Radio.Group value={selectedId} onChange={event => setSelectedId(event.target.value)} style={{ display: "grid", gap: 12, width: "100%" }}>
            {materials.map(material => <Card key={material.id} size="small"><Radio value={material.id}><strong>{material.title}</strong><br />
              <span className="muted">{material.description || `Mã tài liệu: ${material.id}`}</span></Radio></Card>)}
          </Radio.Group>}
        <div style={{ marginTop: 24 }}><p><strong>Số học viên dự kiến</strong></p>
          <InputNumber min={1} max={10000} value={expectedStudents} onChange={value => setExpectedStudents(value ?? 30)} /></div>
        <div style={{ marginTop: 24 }}><Button type="primary" size="large" disabled={!selectedId} loading={submitting} onClick={createSession}>Tạo checkpoint để duyệt</Button></div>
      </>}
    </Card>
  </AppLayout>;
}
