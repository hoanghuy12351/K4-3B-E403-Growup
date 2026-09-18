"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Descriptions, List, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { getDiagnosticSession, startDiagnosticSession, type DiagnosticSession } from "@/services/diagnostic";

export default function CheckpointReviewPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [roomCode, setRoomCode] = useState<string>();

  useEffect(() => {
    getDiagnosticSession(sessionId)
      .then(setSession)
      .catch(reason => setError(reason instanceof Error ? reason.message : "Không thể tải checkpoint."))
      .finally(() => setLoading(false));
  }, [sessionId]);

  async function startClassroom(): Promise<void> {
    setStarting(true);
    setError(null);
    try {
      const result = await startDiagnosticSession(sessionId);
      setRoomCode(result.roomCode);
      setSession(current => current ? { ...current, status: result.status, roomCode: result.roomCode } : current);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể mở lớp. Vui lòng thử lại.");
    } finally {
      setStarting(false);
    }
  }

  return <AppLayout><div className="page-heading"><div><p className="eyebrow">DUYỆT CHECKPOINT</p><h1>{session?.lesson.title || "Đang tải bài giảng"}</h1>
    <p className="muted">Kiểm tra câu hỏi trước khi mở lớp. Giảng viên giữ quyền quyết định.</p></div></div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {loading ? <Spin tip="Đang tải checkpoint..." /> : session && <>
      <Card style={{ marginBottom: 16 }}><Descriptions items={[{ key: "session", label: "Session ID", children: session.sessionId }, { key: "status", label: "Trạng thái", children: <Tag color="blue">{session.status}</Tag> }]} />
        {roomCode ? <Alert type="success" showIcon title="Lớp đã sẵn sàng" description={<div><p>Mã phòng: <strong>{roomCode}</strong></p><p>Session ID: <strong>{session.sessionId}</strong></p><Link href="/join">Mở trang vào lớp cho học viên</Link></div>} /> :
          <Button type="primary" size="large" loading={starting} onClick={startClassroom}>Mở lớp</Button>}
      </Card>
      <List dataSource={session.sections} renderItem={(section, index) => {
        const question = session.questions.find(item => item.sectionId === section.id);
        return <Card key={section.id} title={`Phần ${index + 1}: ${section.title}`} style={{ marginBottom: 16 }}>
          <p><strong>Khái niệm:</strong> {section.concepts.join(", ") || question?.concept || "Chưa xác định"}</p>
          {question ? <><p><strong>Câu hỏi:</strong> {question.question}</p>
            <List size="small" bordered dataSource={question.options} renderItem={option => <List.Item>{option.id}. {option.text}</List.Item>} /></> :
            <Alert type="warning" showIcon title="Chưa có câu hỏi cho phần này" />}
        </Card>;
      }} />
    </>}
  </AppLayout>;
}
