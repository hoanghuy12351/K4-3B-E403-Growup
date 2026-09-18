"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, Input, InputNumber, Steps, Upload, Spin, Tag } from "antd";
import type { UploadProps } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { generateAgentCheckpoints, getPresetDemoCatalog, type AgentGeneratedSession, type PresetDemoCatalog, type PresetDemoSection } from "@/services/diagnostic";

const preparedRequests = [
  "Tạo 3 câu mức trung bình, ưu tiên tình huống thực tế.",
  "Tạo 3 câu tập trung vào các hiểu lầm thường gặp trong phần này.",
  "Tạo 3 câu thiên về khái niệm, tránh câu hỏi định nghĩa.",
];
const ANALYSIS_DELAY_MS = 1200;

export default function NewLessonPage() {
  const router = useRouter();
  const [courseName, setCourseName] = useState("Nhập môn AI cho lớp K4");
  const [slideName, setSlideName] = useState("AI & LLM Foundation.pptx");
  const [catalog, setCatalog] = useState<PresetDemoCatalog | null>(null);
  const [selected, setSelected] = useState<PresetDemoSection | null>(null);
  const [teacherRequest, setTeacherRequest] = useState(preparedRequests[0]);
  const [expectedStudents, setExpectedStudents] = useState(30);
  const [result, setResult] = useState<AgentGeneratedSession | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadProps: UploadProps = {
    accept: ".ppt,.pptx,.pdf",
    maxCount: 1,
    beforeUpload(file) {
      setSlideName(file.name);
      setCatalog(null);
      setSelected(null);
      setResult(null);
      return false;
    },
  };

  async function analyzeSelectedLesson(): Promise<void> {
    setAnalyzing(true);
    setError(null);
    try {
      const [catalogResult] = await Promise.all([
        getPresetDemoCatalog(),
        new Promise<void>(resolve => window.setTimeout(resolve, ANALYSIS_DELAY_MS)),
      ]);
      setCatalog(catalogResult);
      setSelected(catalogResult.sections[0]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể phân tích bài giảng mockup.");
    } finally {
      setAnalyzing(false);
    }
  }

  function chooseSection(section: PresetDemoSection): void {
    setSelected(section);
    setResult(null);
    setError(null);
  }

  async function generate(): Promise<void> {
    if (!selected || !teacherRequest.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      setResult(await generateAgentCheckpoints({ sectionId: selected.id, teacherRequest: teacherRequest.trim(), expectedStudents }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo checkpoint. Vui lòng thử lại.");
    } finally {
      setGenerating(false);
    }
  }

  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">LECTURER FLOW · MOCKUP</p>
      <h1>Tạo khóa học và bài giảng</h1><p className="muted">Luồng mockup: tạo khóa học, tải slide, soạn checkpoint và vào Bục Giảng.</p></div></div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}

    <Card className="course-builder-card">
      <Steps current={result ? 3 : catalog ? 2 : slideName ? 1 : 0} items={[{ title: "Tạo khóa học" }, { title: "Tải bài giảng" }, { title: "Soạn checkpoint" }, { title: "Bục Giảng" }]} />
      <div className="course-builder-grid">
        <section className="builder-panel">
          <p className="eyebrow">1. TẠO KHÓA HỌC</p>
          <Input size="large" value={courseName} onChange={event => setCourseName(event.target.value)} placeholder="Tên khóa học" />
          <p className="muted">Tên khóa học giúp giảng viên quản lý buổi dạy. Trong mockup, dữ liệu được lưu trên trình duyệt.</p>
        </section>
        <section className="builder-panel">
          <p className="eyebrow">2. TẢI LÊN BÀI GIẢNG</p>
          <Upload.Dragger {...uploadProps} className="mock-upload">
            <p className="upload-emoji">📤</p>
            <p><strong>{slideName || "Kéo thả PPTX/PDF vào đây"}</strong></p>
            <p className="muted">Mockup chỉ lấy tên file và dùng dữ liệu slide mẫu để phân tích.</p>
          </Upload.Dragger>
          <Button type="primary" loading={analyzing} onClick={() => void analyzeSelectedLesson()} disabled={!courseName.trim() || !slideName.trim()}>Phân tích bài giảng</Button>
        </section>
      </div>
    </Card>

    {analyzing && <Card className="recent-lesson-card"><div className="agent-message"><Spin /><div><strong>Trợ giảng AI</strong><p>Đang đọc slide mockup, chia phần kiến thức lớn và tìm điểm nên đặt checkpoint...</p></div></div></Card>}

    {catalog && <Card className="recent-lesson-card">
      <div className="agent-message"><Tag color="green">AI</Tag><div><strong>Trợ giảng AI</strong><p>Đã phân tích <strong>{slideName}</strong> trong khóa <strong>{courseName}</strong>. Chọn một phần để soạn nháp câu hỏi/checkpoint.</p></div></div>
      <div className="section-chips">{catalog.sections.map(section => <Button key={section.id} type={selected?.id === section.id ? "primary" : "default"} onClick={() => chooseSection(section)}>{section.title}</Button>)}</div>
      {selected && <>
        <div className="teacher-message"><strong>Giảng viên</strong><p>{selected.title}</p></div>
        <div className="agent-message"><Tag color="green">AI</Tag><div><strong>Trợ giảng AI</strong><p>Phần này tập trung vào: {selected.concepts.join(", ")}.</p><p className="muted">Mục tiêu: {selected.learningObjectives.join(" ")}</p></div></div>
        <div className="agent-message"><Tag color="green">AI</Tag><div><strong>Trợ giảng AI</strong><p>Chọn hướng soạn nháp câu hỏi trắc nghiệm.</p>
          <div className="section-chips">{preparedRequests.map(request => <Button key={request} type={teacherRequest === request ? "primary" : "default"} onClick={() => setTeacherRequest(request)}>{request}</Button>)}</div>
        </div></div>
        <div className="agent-composer"><Input.TextArea value={teacherRequest} onChange={event => setTeacherRequest(event.target.value)} autoSize={{ minRows: 2, maxRows: 4 }} maxLength={2000} placeholder="Ví dụ: Tạo câu tình huống mức trung bình." />
          <div className="composer-actions"><span>Số học viên dự kiến</span><InputNumber min={1} max={10000} value={expectedStudents} onChange={value => setExpectedStudents(value ?? 30)} /><Button type="primary" disabled={!teacherRequest.trim()} loading={generating} onClick={() => void generate()}>Soạn nháp checkpoint</Button></div></div>
        {generating && <div className="agent-message"><Spin size="small" /><div><strong>Trợ giảng AI</strong><p>Đang tạo câu hỏi mockup và chuẩn bị phòng học...</p></div></div>}
        {result && <div className="agent-message"><Tag color="green">AI</Tag><div className="full-width"><strong>Trợ giảng AI</strong><p>{result.agentMessage}</p>
          <Alert type="success" showIcon title="Đã soạn xong checkpoint mockup" description="Giảng viên có thể vào Bục Giảng để tạo phòng học và mở câu hỏi cho học viên." style={{ marginBottom: 12 }} />
          {result.checkpoints.map((checkpoint, index) => <Card key={checkpoint.id} size="small" title={`Câu ${index + 1}`} style={{ marginTop: 12 }}><p><strong>{checkpoint.question}</strong></p>{checkpoint.options.map(option => <p key={option.id}>{option.id}. {option.text}</p>)}</Card>)}
          <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}><Button onClick={() => void generate()} loading={generating}>Soạn lại</Button><Button type="primary" onClick={() => router.push(`/lessons/${result.sessionId}/checkpoints`)}>Vào Bục Giảng</Button></div>
        </div></div>}
      </>}
    </Card>}
  </AppLayout>;
}
