"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Input, Radio, Space, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { getDiagnosticSession, submitDiagnosticResponse, type StudentSession } from "@/services/diagnostic";

export default function StudentDiagnosticPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [session, setSession] = useState<StudentSession | null>(null);
  const [studentId, setStudentId] = useState("student-demo-01");
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    getDiagnosticSession(sessionId).then((value) => { if (active) setSession(value); }).catch((caught: unknown) => {
      if (active) setError(caught instanceof Error ? caught.message : "Không thể tải phiên kiểm tra.");
    });
    return () => { active = false; };
  }, [sessionId]);

  async function submit() {
    const question = session?.questions[current];
    if (!question || !selected || !studentId.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitDiagnosticResponse(sessionId, { studentId: studentId.trim(), questionId: question.id, sectionId: question.sectionId || "", optionId: selected });
      setSelected(null);
      setCurrent((value) => value + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Không thể gửi câu trả lời.");
    } finally {
      setSubmitting(false);
    }
  }

  if (error && !session) return <AppLayout><Alert type="error" showIcon title={error} /></AppLayout>;
  if (!session) return <AppLayout><div className="diagnostic-loading"><Spin /> Đang tải câu hỏi...</div></AppLayout>;
  const question = session.questions[current];
  if (!question) return <AppLayout><Card><h1>Đã gửi tất cả câu trả lời</h1><p className="muted">Cảm ơn bạn. Kết quả tổng hợp sẽ được giảng viên xem sau khi thu đủ phản hồi.</p></Card></AppLayout>;
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">STUDENT DIAGNOSTIC</p><h1>{session.lesson.title}</h1><p className="muted">Câu {current + 1} / {session.questions.length}</p></div><Tag color="blue">{session.status}</Tag></div>
    {error && <Alert className="diagnostic-alert" type="error" showIcon title={error} />}
    <Card className="student-question-card"><Space direction="vertical" size="large" className="diagnostic-stack"><Input aria-label="Student ID" value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="Mã học viên" />
      <div><p className="eyebrow">{question.concept}</p><h2>{question.question}</h2></div>
      <Radio.Group value={selected} onChange={(event) => setSelected(event.target.value)} className="option-group">
        <Space direction="vertical">{question.options.map((option) => <Radio key={option.id} value={option.id}><strong>{option.id}.</strong> {option.text}</Radio>)}</Space>
      </Radio.Group>
      <Button type="primary" onClick={submit} disabled={!selected || !studentId.trim()} loading={submitting}>Gửi câu trả lời</Button>
    </Space></Card>
  </AppLayout>;
}
