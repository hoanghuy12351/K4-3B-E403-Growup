"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Input, Radio, Tag } from "antd";
import type { StudentJoinInput } from "@/types/user";
import { getRoomState, joinRoom, submitStudentResponse, type ActiveQuestion, type RoomJoinResult } from "@/services/diagnostic";

type JoinedStudent = StudentJoinInput & RoomJoinResult;

export default function JoinPage() {
  const [joined, setJoined] = useState<JoinedStudent | null>(null);
  const [question, setQuestion] = useState<ActiveQuestion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!joined) return;
    let active = true;
    const poll = async (): Promise<void> => {
      try {
        const state = await getRoomState(joined.roomCode, joined.participantId);
        if (active) setQuestion(state.activeQuestion);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "Không thể cập nhật trạng thái lớp.");
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 2000);
    return () => { active = false; window.clearInterval(timer); };
  }, [joined]);

  if (joined) return <main className="join-page"><section className="join-shell"><Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link>
    <Card className="join-success"><Tag color="green">Đã vào lớp</Tag><h1>Chào {joined.displayName}</h1>{error && <Alert type="error" showIcon description={error} style={{ marginBottom: 16 }} />}
      {!question ? <><p>Đã vào lớp với mã <strong>{joined.roomCode}</strong>. Đang chờ giảng viên mở checkpoint...</p><Alert type="info" showIcon title="Bạn không cần tài khoản" description="Tên hiển thị chỉ dùng trong lượt kiểm tra này." /></> : <StudentQuestion key={question.id} joined={joined} question={question} submitting={submitting} setSubmitting={setSubmitting} setError={setError} />}
      <Button style={{ marginTop: 20 }} onClick={() => setJoined(null)}>Đổi mã hoặc tên</Button>
    </Card></section></main>;

  return <main className="join-page"><section className="join-shell"><Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link><div className="join-copy"><p className="eyebrow">DÀNH CHO HỌC VIÊN</p><h1>Vào lượt kiểm tra</h1><p>Nhập mã giảng viên cung cấp và tên hiển thị. Bạn không cần đăng ký hoặc đăng nhập.</p></div>
    <Card className="join-card">{error && <Alert type="error" showIcon title="Không thể vào lớp" description={error} />}
      <Form<StudentJoinInput> layout="vertical" requiredMark={false} onFinish={async values => { setError(null); const sessionCode = values.sessionCode.trim().toUpperCase(); const displayName = values.displayName.trim(); try { const result = await joinRoom(sessionCode, displayName); setJoined({ sessionCode, displayName, ...result }); } catch (reason) { setError(reason instanceof Error ? reason.message : "Vui lòng kiểm tra mã phòng và thử lại."); } }}>
        <Form.Item name="sessionCode" label="Mã lượt kiểm tra" normalize={value => String(value).toUpperCase()} rules={[{ required: true, whitespace: true, message: "Nhập mã lượt kiểm tra." }]}><Input size="large" maxLength={12} placeholder="Ví dụ: GX-AB12" autoComplete="off" /></Form.Item>
        <Form.Item name="displayName" label="Tên hiển thị" rules={[{ required: true, whitespace: true, message: "Nhập tên hiển thị." }, { min: 2, max: 50, message: "Tên cần từ 2 đến 50 ký tự." }]}><Input size="large" maxLength={50} placeholder="Ví dụ: Minh Anh" autoComplete="off" /></Form.Item>
        <Button size="large" type="primary" htmlType="submit" block>Vào lớp</Button>
      </Form><p className="join-privacy">Growup không yêu cầu email hoặc mật khẩu của học viên.</p>
    </Card><Link className="back-link" href="/">Quay lại trang giới thiệu</Link></section></main>;
}

function StudentQuestion({ joined, question, submitting, setSubmitting, setError }: { joined: JoinedStudent; question: ActiveQuestion; submitting: boolean; setSubmitting: (value: boolean) => void; setError: (value: string | null) => void }) {
  const [optionId, setOptionId] = useState<string>();
  const [explanation, setExplanation] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const submit = async (): Promise<void> => {
    if (!optionId) return;
    setSubmitting(true); setError(null);
    try { await submitStudentResponse(joined.sessionId, { participantId: joined.participantId, questionId: question.id, sectionId: question.sectionId, optionId, explanation: explanation.trim() || undefined }); setSubmitted(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể gửi câu trả lời."); }
    finally { setSubmitting(false); }
  };
  return <><p className="eyebrow">CHECKPOINT ĐANG MỞ</p><h2>{question.question}</h2><Radio.Group value={optionId} onChange={event => setOptionId(event.target.value)} style={{ display: "grid", gap: 10, width: "100%" }}>{question.options.map(option => <Radio key={option.id} value={option.id}>{option.id}. {option.text}</Radio>)}</Radio.Group>
    <Input.TextArea value={explanation} onChange={event => setExplanation(event.target.value)} placeholder="Giải thích ngắn (không bắt buộc)" maxLength={2000} autoSize={{ minRows: 3 }} style={{ marginTop: 16 }} />
    {submitted ? <Alert type="success" showIcon title="Đã gửi câu trả lời" description="Bạn có thể thay đổi câu trả lời khi checkpoint vẫn còn mở." style={{ marginTop: 16 }} /> : null}
    <Button type="primary" block size="large" disabled={!optionId} loading={submitting} onClick={() => void submit()} style={{ marginTop: 16 }}>{submitted ? "Cập nhật câu trả lời" : "Gửi câu trả lời"}</Button>
  </>;
}
