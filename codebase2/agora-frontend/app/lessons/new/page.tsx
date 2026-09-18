"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, Input, InputNumber, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { generateAgentCheckpoints, getPresetDemoCatalog, type AgentGeneratedSession, type PresetDemoCatalog, type PresetDemoSection } from "@/services/diagnostic";

const preparedRequests = [
  "Tạo 3 câu mức trung bình, ưu tiên tình huống thực tế.",
  "Tạo 3 câu tập trung vào các misconception trong phần này.",
  "Tạo 3 câu thiên về khái niệm, tránh câu hỏi định nghĩa.",
];
const ANALYSIS_DELAY_MS = 15_000;

export default function NewLessonPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<PresetDemoCatalog | null>(null);
  const [selected, setSelected] = useState<PresetDemoSection | null>(null);
  const [teacherRequest, setTeacherRequest] = useState("");
  const [expectedStudents, setExpectedStudents] = useState(30);
  const [result, setResult] = useState<AgentGeneratedSession | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyzeSelectedLesson(): Promise<void> {
    setAnalyzing(true);
    setError(null);
    try {
      // Keep the analysis state visible long enough for the classroom demo.
      const [catalogResult] = await Promise.all([
        getPresetDemoCatalog(),
        new Promise<void>(resolve => window.setTimeout(resolve, ANALYSIS_DELAY_MS)),
      ]);
      setCatalog(catalogResult);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể phân tích bài giảng demo.");
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

  return <AppLayout><div className="page-heading"><div><p className="eyebrow">TEACHING AGENT</p>
    <h1>Chuẩn bị checkpoint bằng hội thoại</h1><p className="muted">Teaching Agent chỉ đề xuất câu hỏi; giảng viên luôn duyệt và quyết định mở lớp.</p></div></div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {!catalog && !analyzing && <Card className="recent-lesson-card" title="Chọn slide để phân tích"><p>Chọn bài giảng demo mà Teaching Agent sẽ dùng để chuẩn bị checkpoint.</p>
      <Card size="small"><strong>AI & LLM Foundation</strong><p className="muted">Bộ slide demo đã có dữ liệu phân tích sẵn, không cần tải tài liệu lên.</p><Button type="primary" onClick={() => void analyzeSelectedLesson()}>Chọn bài giảng này</Button></Card>
    </Card>}
    {analyzing && <Card className="recent-lesson-card"><div className="agent-message"><Spin /><div><strong>Teaching Agent</strong><p>Đang phân tích bài AI & LLM Foundation để xác định các phần kiến thức và misconception...</p></div></div></Card>}
    {catalog && <Card className="recent-lesson-card">
      <div className="agent-message"><Tag color="green">G</Tag><div><strong>Teaching Agent</strong><p>Em đã phân tích xong bài <strong>{catalog.lesson.title}</strong> thành 8 phần. Thầy/cô muốn kiểm tra phần nào?</p></div></div>
      <div className="section-chips">{catalog.sections.map(section => <Button key={section.id} type={selected?.id === section.id ? "primary" : "default"} onClick={() => chooseSection(section)}>{section.title}</Button>)}</div>
      {selected && <>
        <div className="teacher-message"><strong>Giảng viên</strong><p>{selected.title}</p></div>
        <div className="agent-message"><Tag color="green">G</Tag><div><strong>Teaching Agent</strong><p>Phần này tập trung vào: {selected.concepts.join(", ")}.</p><p className="muted">Mục tiêu: {selected.learningObjectives.join(" ")}</p></div></div>
        <div className="agent-message"><Tag color="green">G</Tag><div><strong>Teaching Agent</strong><p>Thầy/cô muốn kiểm tra học viên theo hướng nào?</p>
          <div className="section-chips">{preparedRequests.map(request => <Button key={request} type={teacherRequest === request ? "primary" : "default"} onClick={() => setTeacherRequest(request)}>{request}</Button>)}</div>
        </div></div>
        {teacherRequest && <div className="teacher-message"><strong>Giảng viên</strong><p>{teacherRequest}</p></div>}
        {generating && <div className="agent-message"><Spin size="small" /><div><strong>Teaching Agent</strong><p>Đang tạo checkpoint từ nội dung bài giảng đã phân tích...</p></div></div>}
        {result && <div className="agent-message"><Tag color="green">G</Tag><div className="full-width"><strong>Teaching Agent</strong><p>{result.agentMessage}</p>
          {result.generation.fallbackUsed && <Alert type="warning" showIcon title="Đang dùng câu dự phòng" description="Provider không hoàn tất tạo câu mới; các câu xem trước được lấy từ bộ demo đã kiểm tra." style={{ marginBottom: 12 }} />}
          {result.checkpoints.map((checkpoint, index) => <Card key={checkpoint.id} size="small" title={`Checkpoint ${index + 1}`} style={{ marginTop: 12 }}><p><strong>{checkpoint.question}</strong></p>{checkpoint.options.map(option => <p key={option.id}>{option.id}. {option.text}</p>)}<small>Nguồn slide: {(checkpoint.sourceRefs ?? []).map(source => source.id).join(", ")}</small></Card>)}
          <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}><Button onClick={() => void generate()} loading={generating}>Tạo lại</Button><Button type="primary" onClick={() => router.push(`/lessons/${result.sessionId}/checkpoints`)}>Duyệt & mở lớp</Button></div>
        </div></div>}
      </>}
      <div className="agent-composer"><Input.TextArea value={teacherRequest} onChange={event => setTeacherRequest(event.target.value)} autoSize={{ minRows: 2, maxRows: 4 }} maxLength={2000} placeholder="Ví dụ: Tạo câu tình huống mức trung bình, tránh câu hỏi định nghĩa." />
        <div className="composer-actions"><span>Số học viên dự kiến</span><InputNumber min={1} max={10000} value={expectedStudents} onChange={value => setExpectedStudents(value ?? 30)} /><Button type="primary" disabled={!selected || !teacherRequest.trim()} loading={generating} onClick={() => void generate()}>Gửi yêu cầu</Button></div></div>
    </Card>}
  </AppLayout>;
}
