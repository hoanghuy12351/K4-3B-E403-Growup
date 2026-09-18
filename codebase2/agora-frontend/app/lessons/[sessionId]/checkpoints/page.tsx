"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Descriptions, Progress, QRCode, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { closeLiveCheckpoint, getDiagnosticSession, getDiagnosticSummary, startDiagnosticSession, triggerLiveCheckpoint, updateLiveState, type DiagnosticSession, type DiagnosticSummary, type LiveCheckpointPlan } from "@/services/diagnostic";
import { API_URL } from "@/services/api";

const recommendationText = { reteach: "Nên giảng lại ngắn phần này trước khi chuyển tiếp.", clarify: "Nên làm rõ thêm một vài ý trước khi tiếp tục.", continue: "Lớp đang theo kịp, có thể tiếp tục bài học.", insufficient_data: "Chưa đủ phản hồi để kết luận." };
const recommendationColor = { reteach: "red", clarify: "orange", continue: "green", insufficient_data: "blue" } as const;

function transcriptNumber(ref: string | null | undefined): number { return Number(ref?.split("-")[1] || 0); }

export default function LiveTeachingPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const triggerInFlight = useRef(new Set<string>());

  const load = useCallback(async (): Promise<void> => {
    try {
      const next = await getDiagnosticSession(sessionId);
      setSession(next);
      if (next.status !== "draft") setSummary(await getDiagnosticSummary(sessionId));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tải phòng học."); }
    finally { setLoading(false); }
  }, [sessionId]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => {
    if (!session || session.status === "draft") return;
    const timer = window.setInterval(() => void load(), 1500);
    return () => window.clearInterval(timer);
  }, [session, load]);

  const plans = session?.checkpointPlans || [];
  const openPlan = plans.find(plan => plan.status === "open");
  const generatingPlan = plans.find(plan => plan.status === "generating");
  const failedPlan = plans.find(plan => plan.status === "failed");
  const pendingPlan = plans.find(plan => plan.status === "planned");
  const currentPlan = openPlan || generatingPlan || failedPlan || pendingPlan;
  const joinUrl = typeof window === "undefined" ? "/join" : `${window.location.origin}/join`;
  const currentResult = useMemo(() => {
    if (!currentPlan || !summary) return null;
    return summary.sectionResults.find(item => session?.sections.some(section => section.id === item.sectionId && section.originalSectionId === currentPlan.sectionId)) || null;
  }, [currentPlan, session?.sections, summary]);

  async function startClassroom(): Promise<void> {
    setWorking("start"); setError(null);
    try { await startDiagnosticSession(sessionId); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tạo lớp học."); }
    finally { setWorking(null); }
  }

  async function advanceSlide(): Promise<void> {
    if (!session || openPlan || generatingPlan) return;
    const current = session.currentSlide || 1;
    if (current >= 29) return;
    setWorking("slide"); setError(null);
    try {
      const ref = session.currentTranscriptRef || session.nextTranscriptRef;
      if (!ref) throw new Error("Không còn transcript để phát.");
      await updateLiveState(sessionId, { currentSlide: current + 1, currentTranscriptRef: ref });
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể cập nhật slide."); }
    finally { setWorking(null); }
  }

  const generatePlan = useCallback(async (plan: LiveCheckpointPlan): Promise<void> => {
    if (triggerInFlight.current.has(plan.id)) return;
    triggerInFlight.current.add(plan.id); setWorking(plan.id); setError(null);
    try { await triggerLiveCheckpoint(sessionId, plan.id); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tạo câu hỏi checkpoint."); await load(); }
    finally { triggerInFlight.current.delete(plan.id); setWorking(null); }
  }, [load, sessionId]);

  async function closePlan(plan: LiveCheckpointPlan): Promise<void> {
    setWorking(plan.id); setError(null);
    try { await closeLiveCheckpoint(sessionId, plan.id); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể đóng checkpoint."); }
    finally { setWorking(null); }
  }

  useEffect(() => {
    if (!session || session.status === "draft" || openPlan || generatingPlan || !session.nextTranscriptRef) return;
    const timer = window.setTimeout(async () => {
      try {
        await updateLiveState(sessionId, { currentSlide: session.currentSlide || 1, currentTranscriptRef: session.nextTranscriptRef as string });
        await load();
      } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể cập nhật transcript trực tiếp."); }
    }, 650);
    return () => window.clearTimeout(timer);
  }, [generatingPlan, load, openPlan, session, sessionId]);

  useEffect(() => {
    if (!session || !pendingPlan || openPlan || generatingPlan || pendingPlan.status !== "planned") return;
    const reached = (session.currentSlide || 0) >= pendingPlan.triggerSlide && transcriptNumber(session.currentTranscriptRef) >= transcriptNumber(pendingPlan.requiredTranscriptRef);
    if (!reached) return;
    const timer = window.setTimeout(() => void generatePlan(pendingPlan), 0);
    return () => window.clearTimeout(timer);
  }, [generatePlan, generatingPlan, openPlan, pendingPlan, session]);

  const statusText = generatingPlan ? "Đang tạo câu hỏi từ nội dung vừa giảng..." : openPlan ? "Đang chờ phản hồi" : "Đang nghe bài giảng";
  const transcript = session?.visibleTranscript || [];
  const slideUrl = `${API_URL}/api/teaching-agent/live-lesson/slides#page=${session?.currentSlide || 1}&view=FitH`;

  return <AppLayout>
    <div className="page-heading live-heading"><div><p className="eyebrow">PHÒNG DẠY TRỰC TIẾP</p><h1>{session?.lesson.title || "Đang tải bài giảng"}</h1><p className="muted">Transcript chỉ hiện dần theo nhịp giảng và checkpoint dùng đúng phần nội dung đã xuất hiện.</p></div>{session?.roomCode && <div className="live-room-code"><span>Mã phòng</span><strong>{session.roomCode}</strong></div>}</div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {loading ? <Spin tip="Đang tải phòng học..." /> : session && <div className="live-classroom-grid">
      <section className="teacher-stage"><Card className="live-stage-card">
        <div className="stage-topline"><Tag color={session.status === "live" ? "red" : session.status === "ready" ? "green" : "blue"}>{session.status === "draft" ? "Bản nháp" : session.status === "ready" ? "Sẵn sàng" : "Đang dạy"}</Tag><span>Slide {session.currentSlide || 1} / 29</span></div>
        <iframe key={session.currentSlide || 1} title={`Slide ${session.currentSlide || 1}`} src={slideUrl} style={{ width: "100%", height: 500, border: "1px solid #e5e5e5", borderRadius: 12, margin: "12px 0" }} />
        <h2>{currentPlan?.sectionTitle || "Đang bắt đầu bài giảng"}</h2><p className="stage-objective">{statusText}</p>
        {currentPlan && <Card size="small" title="Checkpoint hiện tại"><p><strong>Trigger slide {currentPlan.triggerSlide}</strong></p><p className="muted">Yêu cầu giảng viên: {currentPlan.teacherPrompt}</p>{currentPlan.status === "failed" && <Button type="primary" loading={working === currentPlan.id} onClick={() => void generatePlan(currentPlan)}>Thử tạo lại câu hỏi</Button>}{currentPlan.status === "open" && <Button danger loading={working === currentPlan.id} onClick={() => void closePlan(currentPlan)}>Đóng checkpoint</Button>}</Card>}
        <div className="stage-controls">{session.status === "draft" ? <Button type="primary" size="large" loading={working === "start"} onClick={() => void startClassroom()}>Bắt đầu lớp học</Button> : <Button type="primary" size="large" disabled={Boolean(openPlan || generatingPlan) || (session.currentSlide || 1) >= 29} loading={working === "slide"} onClick={() => void advanceSlide()}>Slide tiếp theo</Button>}</div>
      </Card></section>
      <aside className="live-side-panel">
        <Card className="student-join-card" title="Học viên vào lớp"><QRCode value={joinUrl} size={128} bordered={false} /><Descriptions column={1} size="small" items={[{ key: "code", label: "Mã phòng", children: <strong>{session.roomCode}</strong> }, { key: "link", label: "Trang vào lớp", children: <Link href="/join">/join</Link> }]} /></Card>
        <Card title="Live transcription"><Tag color={generatingPlan ? "gold" : "green"}>{statusText}</Tag><div style={{ maxHeight: 260, overflowY: "auto", marginTop: 12 }}>{transcript.length ? transcript.slice(-8).map(item => <p key={item.ref}><strong>{item.ref}</strong> {item.text}</p>) : <p className="muted">Đang chờ lời giảng đầu tiên...</p>}</div></Card>
        <Card className="live-response-card" title="Tín hiệu lớp học">{currentResult ? <><div className="response-number"><strong>{currentResult.totalResponses}</strong><span>phản hồi tại checkpoint</span></div><Progress percent={Math.round(currentResult.correctRate * 100)} strokeColor="#58cc02" /><Tag color={recommendationColor[summary?.recommendation || "insufficient_data"]}>{recommendationText[summary?.recommendation || "insufficient_data"]}</Tag><p className="muted">{currentResult.dominantMisconception?.statement || summary?.reason}</p></> : <p className="muted">Kết quả phản hồi sẽ xuất hiện khi học viên trả lời.</p>}</Card>
        <Card className="slide-list-card" title="Các checkpoint">{plans.map(plan => <div key={plan.id} style={{ marginBottom: 10 }}><strong>{plan.order}. {plan.sectionTitle}</strong><div><Tag color={plan.status === "open" ? "green" : plan.status === "failed" ? "red" : plan.status === "generating" ? "gold" : "blue"}>{plan.status}</Tag> Slide {plan.triggerSlide}</div></div>)}</Card>
      </aside>
    </div>}
  </AppLayout>;
}
