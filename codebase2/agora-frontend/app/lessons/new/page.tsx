"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, Checkbox, Input, InputNumber, Spin, Steps, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { createLiveSession, getPresetDemoCatalog, type PresetDemoCatalog } from "@/services/diagnostic";
import { USE_MOCK } from "@/services/api";

const defaultPrompt = "Tạo một câu hỏi khái niệm mức trung bình dựa trên phần vừa giảng.";

export default function NewLessonPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<PresetDemoCatalog | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [prompts, setPrompts] = useState<Record<string, string>>({});
  const [expectedStudents, setExpectedStudents] = useState(30);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyzeLesson(): Promise<void> {
    setLoading(true); setError(null);
    try {
      const next = await getPresetDemoCatalog();
      setCatalog(next); setSelectedIds([]); setPrompts({});
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải dữ liệu bài giảng.");
    } finally { setLoading(false); }
  }

  function toggleSection(sectionId: string, checked: boolean): void {
    setSelectedIds(current => checked ? [...current, sectionId] : current.filter(id => id !== sectionId));
    setPrompts(current => ({ ...current, [sectionId]: current[sectionId] || defaultPrompt }));
  }

  async function prepareLiveClass(): Promise<void> {
    if (!catalog || !selectedIds.length) return;
    setCreating(true); setError(null);
    try {
      const selected = catalog.sections.filter(section => selectedIds.includes(section.id));
      const result = await createLiveSession({
        lessonId: catalog.lesson.id, expectedStudents,
        checkpointSelections: selected.map(section => ({ sectionId: section.id, teacherPrompt: (prompts[section.id] || defaultPrompt).trim(), triggerSlide: section.triggerSlide })),
      });
      router.push(`/lessons/${result.sessionId}/checkpoints`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể chuẩn bị lớp học trực tiếp.");
    } finally { setCreating(false); }
  }

  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">LECTURER FLOW · LIVE CLASS</p><h1>Chuẩn bị lớp học trực tiếp</h1><p className="muted">Chọn các mốc trong bài giảng. Câu hỏi chỉ được tạo khi lớp thực sự đến từng checkpoint.</p></div></div>
    {USE_MOCK && <Alert type="warning" showIcon title="Cần backend thật" description="Luồng checkpoint trực tiếp dùng LLM đã cấu hình. Đặt NEXT_PUBLIC_USE_MOCK=false để chuẩn bị lớp." style={{ marginBottom: 16 }} />}
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    <Card className="course-builder-card">
      <Steps current={catalog ? 1 : 0} items={[{ title: "Phân tích bài giảng" }, { title: "Chọn checkpoint" }, { title: "Bục Giảng" }]} />
      <div className="course-builder-grid">
        <section className="builder-panel"><p className="eyebrow">BÀI GIẢNG MẪU</p><h3>AI & LLM Foundation</h3><p className="muted">Dùng slide và transcript đã được phân tích sẵn trong kho dữ liệu của dự án.</p><Button type="primary" loading={loading} onClick={() => void analyzeLesson()}>Phân tích bài giảng</Button></section>
        <section className="builder-panel"><p className="eyebrow">QUY MÔ LỚP</p><InputNumber min={1} max={10000} value={expectedStudents} onChange={value => setExpectedStudents(value ?? 30)} /><p className="muted">Số này được dùng để đánh giá mức độ phủ phản hồi của lớp.</p></section>
      </div>
    </Card>
    {loading && <Card className="recent-lesson-card"><Spin /> Đang đọc timeline bài giảng...</Card>}
    {catalog && <Card className="recent-lesson-card" title="Timeline checkpoint">
      <p className="muted">Có thể chọn nhiều phần. Thứ tự checkpoint luôn theo thứ tự bài giảng.</p>
      {catalog.sections.map(section => {
        const selected = selectedIds.includes(section.id);
        return <Card key={section.id} size="small" style={{ marginTop: 12, borderColor: selected ? "#58cc02" : undefined }}>
          <Checkbox checked={selected} onChange={event => toggleSection(section.id, event.target.checked)}><strong>{section.title}</strong></Checkbox>
          <div className="muted" style={{ margin: "8px 0" }}>Slide {section.slidePages?.join(", ")} · Trigger slide {section.triggerSlide}</div>
          {selected && <><div><Tag color="green">Checkpoint đã chọn</Tag></div><Input.TextArea value={prompts[section.id] || defaultPrompt} onChange={event => setPrompts(current => ({ ...current, [section.id]: event.target.value }))} maxLength={2000} autoSize={{ minRows: 2, maxRows: 4 }} style={{ marginTop: 10 }} /></>}
        </Card>;
      })}
      <div className="composer-actions" style={{ marginTop: 16 }}><span>{selectedIds.length} checkpoint đã chọn</span><Button type="primary" loading={creating} disabled={USE_MOCK || !selectedIds.length || selectedIds.some(id => !(prompts[id] || defaultPrompt).trim())} onClick={() => void prepareLiveClass()}>Chuẩn bị lớp trực tiếp</Button></div>
    </Card>}
  </AppLayout>;
}
