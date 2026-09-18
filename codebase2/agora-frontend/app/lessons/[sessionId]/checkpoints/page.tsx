"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Descriptions, List, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { closeCheckpoint, getDiagnosticSession, getDiagnosticSummary, openCheckpoint, startDiagnosticSession, type DiagnosticSession, type DiagnosticSummary } from "@/services/diagnostic";

const recommendationText = {
  reteach: "Dữ liệu hiện tại cho thấy phần này nên được giảng lại ngắn.",
  clarify: "Có một số tín hiệu chưa chắc chắn. Nên làm rõ trước khi tiếp tục.",
  continue: "Phần lớn phản hồi cho thấy lớp đang theo kịp. Có thể tiếp tục.",
  insufficient_data: "Chưa đủ phản hồi để kết luận.",
};

export default function CheckpointReviewPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [workingQuestion, setWorkingQuestion] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    try {
      const next = await getDiagnosticSession(sessionId);
      setSession(next);
      if (next.status !== "draft") setSummary(await getDiagnosticSummary(sessionId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải checkpoint.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);
  const classroomStarted = session?.status !== undefined && session.status !== "draft";
  useEffect(() => {
    if (!classroomStarted) return;
    const timer = window.setInterval(() => void load(), 2000);
    return () => window.clearInterval(timer);
  }, [classroomStarted, load]);

  async function startClassroom(): Promise<void> {
    setWorkingQuestion("start"); setError(null);
    try { await startDiagnosticSession(sessionId); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể mở lớp."); } finally { setWorkingQuestion(null); }
  }

  async function control(questionId: string, action: "open" | "close"): Promise<void> {
    setWorkingQuestion(questionId); setError(null);
    try { if (action === "open") await openCheckpoint(sessionId, questionId); else await closeCheckpoint(sessionId, questionId); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể cập nhật checkpoint."); } finally { setWorkingQuestion(null); }
  }

  const activeResult = summary?.sectionResults.find(item => item.sectionId === session?.sections.find(section => session.questions.find(question => question.id === session.activeQuestionId && question.sectionId === section.id))?.id);
  return <AppLayout><div className="page-heading"><div><p className="eyebrow">TEACHING AGENT LIVE</p><h1>{session?.lesson.title || "Đang tải bài giảng"}</h1><p className="muted">Teaching Agent đề xuất từ dữ liệu lớp; giảng viên quyết định bước dạy tiếp theo.</p></div></div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {loading ? <Spin tip="Đang tải checkpoint..." /> : session && <>
      <Card style={{ marginBottom: 16 }}><Descriptions items={[{ key: "room", label: "Mã phòng", children: <strong>{session.roomCode}</strong> }, { key: "status", label: "Trạng thái", children: <Tag color={session.status === "live" ? "red" : "blue"}>{session.status}</Tag> }]} />
        {session.status === "draft" ? <Button type="primary" size="large" loading={workingQuestion === "start"} onClick={() => void startClassroom()}>Mở lớp</Button> : <Alert type="success" showIcon title="Lớp đã sẵn sàng" description={<span>Chia sẻ mã <strong>{session.roomCode}</strong> và <Link href="/join">mở trang vào lớp cho học viên</Link>.</span>} />}
      </Card>
      {session.status !== "draft" && summary && <Card title="Gợi ý cho giảng viên" style={{ marginBottom: 16 }}><p><strong>{recommendationText[summary.recommendation]}</strong></p><p className="muted">{summary.reason}</p>{activeResult && <p>{activeResult.totalResponses} phản hồi, đúng {Math.round(activeResult.correctRate * 100)}%. {activeResult.dominantMisconception?.statement ? `Misconception nổi bật: ${activeResult.dominantMisconception.statement}` : ""}</p>}<Button>Giảng lại</Button><Button style={{ marginLeft: 10 }}>Tiếp tục</Button></Card>}
      <List dataSource={session.sections} renderItem={(section, index) => {
        const question = session.questions.find(item => item.sectionId === section.id);
        if (!question) return null;
        const isActive = session.activeQuestionId === question.id;
        const result = summary?.sectionResults.find(item => item.sectionId === section.id);
        return <Card key={section.id} title={`Checkpoint ${index + 1}: ${section.title}`} style={{ marginBottom: 16 }} extra={isActive ? <Tag color="red">Đang mở</Tag> : null}>
          <p><strong>Khái niệm:</strong> {section.concepts.join(", ") || question.concept}</p><p><strong>{question.question}</strong></p><List size="small" bordered dataSource={question.options} renderItem={option => <List.Item>{option.id}. {option.text}</List.Item>} />
          {result && <p className="muted" style={{ marginTop: 12 }}>{result.totalResponses} phản hồi đã nhận.</p>}
          {session.status !== "draft" && (isActive ? <Button danger loading={workingQuestion === question.id} onClick={() => void control(question.id, "close")}>Đóng checkpoint</Button> : <Button type="primary" loading={workingQuestion === question.id} onClick={() => void control(question.id, "open")}>Mở checkpoint</Button>)}
        </Card>;
      }} />
    </>}
  </AppLayout>;
}
