"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, InputNumber, Radio, Spin } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { createDiagnosticSession, createPresetDemoCheckpoint, getPresetDemoCatalog, listLessonMaterials, uploadLessonMaterial, type LessonMaterial, type PresetDemoCatalog } from "@/services/diagnostic";

export default function NewLessonPage() {
  const router = useRouter();
  const [materials, setMaterials] = useState<LessonMaterial[]>([]);
  const [presetDemo, setPresetDemo] = useState<PresetDemoCatalog | null>(null);
  const [selectedId, setSelectedId] = useState<string>();
  const [selectedSectionId, setSelectedSectionId] = useState<string>();
  const [selectedSource, setSelectedSource] = useState<"preset" | "material">("preset");
  const [expectedStudents, setExpectedStudents] = useState(30);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listLessonMaterials(), getPresetDemoCatalog()])
      .then(([items, demo]) => {
        setMaterials(items);
        setSelectedId(items[0]?.id);
        setPresetDemo(demo);
        setSelectedSectionId(demo.sections[0]?.id);
      })
      .catch(reason => setError(reason instanceof Error ? reason.message : "Không thể tải lựa chọn bài giảng."))
      .finally(() => setLoading(false));
  }, []);

  async function createSession(): Promise<void> {
    if (selectedSource === "preset" && !selectedSectionId) return;
    if (selectedSource === "material" && !selectedId) return;
    setError(null);
    setSubmitting(true);
    try {
      const session = selectedSource === "preset"
        ? await createPresetDemoCheckpoint(selectedSectionId as string, expectedStudents)
        : await createDiagnosticSession(selectedId as string, expectedStudents);
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

  const canCreate = selectedSource === "preset" ? Boolean(selectedSectionId) : Boolean(selectedId);

  return <AppLayout><div className="page-heading"><div><p className="eyebrow">BÀI GIẢNG MỚI</p><h1>Chọn tài liệu bài giảng</h1>
    <p className="muted">Chọn bài giảng và phần kiến thức cần kiểm tra trước khi mở lớp.</p></div></div>
    <Card title="Tải tài liệu mới" className="recent-lesson-card" style={{ marginBottom: 16 }}>
      <p className="muted">Hỗ trợ PDF hoặc PPTX, tối đa 25 MB. Hệ thống chỉ trích xuất văn bản có trong tài liệu.</p>
      <input type="file" accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation" onChange={event => setFile(event.target.files?.[0] ?? null)} />
      <Button style={{ marginLeft: 12 }} loading={uploading} disabled={!file} onClick={upload}>Tải tài liệu lên</Button>
    </Card>
    <Card title="Chọn nguồn tạo checkpoint" className="recent-lesson-card">
      {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
      {loading ? <Spin tip="Đang tải tài liệu..." /> : <>
        {presetDemo && <Card size="small" style={{ marginBottom: 16, borderColor: selectedSource === "preset" ? "#1677ff" : undefined }}>
          <Radio checked={selectedSource === "preset"} onChange={() => setSelectedSource("preset")}><strong>{presetDemo.lesson.title}</strong><br />
            <span className="muted">Bài giảng đã có checkpoint để giảng viên lựa chọn và duyệt.</span></Radio>
          {selectedSource === "preset" && <div style={{ marginTop: 16 }}>
            <p><strong>Chọn phần kiến thức cần tạo checkpoint</strong></p>
            <Radio.Group value={selectedSectionId} onChange={event => setSelectedSectionId(event.target.value)} style={{ display: "grid", gap: 8, width: "100%" }}>
              {presetDemo.sections.map(section => <Radio key={section.id} value={section.id}>{section.title}</Radio>)}
            </Radio.Group>
          </div>}
        </Card>}
        {materials.length === 0 ? <Alert type="info" showIcon title="Chưa có tài liệu đã tải" description="Bạn có thể chọn bài giảng có sẵn ở trên hoặc tải thêm PDF/PPTX." /> :
          <Radio.Group value={selectedSource === "material" ? selectedId : undefined} onChange={event => { setSelectedSource("material"); setSelectedId(event.target.value); }} style={{ display: "grid", gap: 12, width: "100%" }}>
            {materials.map(material => <Card key={material.id} size="small"><Radio value={material.id}><strong>{material.title}</strong><br />
              <span className="muted">{material.description || `Mã tài liệu: ${material.id}`}</span></Radio></Card>)}
          </Radio.Group>}
        <div style={{ marginTop: 24 }}><p><strong>Số học viên dự kiến</strong></p>
          <InputNumber min={1} max={10000} value={expectedStudents} onChange={value => setExpectedStudents(value ?? 30)} /></div>
        <div style={{ marginTop: 24 }}><Button type="primary" size="large" disabled={!canCreate} loading={submitting} onClick={createSession}>Tạo checkpoint để duyệt</Button></div>
      </>}
    </Card>
  </AppLayout>;
}
