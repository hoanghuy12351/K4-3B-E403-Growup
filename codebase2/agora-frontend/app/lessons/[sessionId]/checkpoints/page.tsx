"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Descriptions, Input, Progress, QRCode, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { closeLiveCheckpoint, getDiagnosticSession, getDiagnosticSummary, openLiveCheckpoint, regenerateLiveCheckpoint, startDiagnosticSession, triggerLiveCheckpoint, updateLiveState, type DiagnosticSession, type DiagnosticSummary, type LiveCheckpointPlan } from "@/services/diagnostic";
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
  const [revisionPrompts, setRevisionPrompts] = useState<Record<string, string>>({});
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
  const previewPlan = plans.find(plan => plan.status === "preview");
  const failedPlan = plans.find(plan => plan.status === "failed");
  const pendingPlan = plans.find(plan => plan.status === "planned");
  const currentPlan = openPlan || generatingPlan || previewPlan || failedPlan || pendingPlan;
  const latestClosedPlan = [...plans].reverse().find(plan => plan.status === "closed");
  const resultPlan = openPlan || latestClosedPlan || currentPlan;
  const previewQuestions = session?.checkpointPreviews?.find(item => item.planId === currentPlan?.id)?.questions || [];
  const joinUrl = typeof window === "undefined" ? "/join" : `${window.location.origin}/join`;
  const currentResult = useMemo(() => {
    if (!resultPlan || !summary) return null;
    return summary.sectionResults.find(item => session?.sections.some(section => section.id === item.sectionId && section.originalSectionId === resultPlan.sectionId)) || null;
  }, [resultPlan, session?.sections, summary]);
  const correctRate = Math.round((currentResult?.correctRate ?? 0) * 100);
  const activeRecommendation = currentResult?.recommendation ?? summary?.recommendation ?? "insufficient_data";
  const correctAnswer = resultPlan?.status === "closed"
    ? currentResult?.optionDistribution.find(option => option.correct)
    : undefined;

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

  async function openPlanToStudents(plan: LiveCheckpointPlan): Promise<void> {
    setWorking(plan.id); setError(null);
    try { await openLiveCheckpoint(sessionId, plan.id); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể mở checkpoint cho học viên."); }
    finally { setWorking(null); }
  }

  async function regeneratePlan(plan: LiveCheckpointPlan): Promise<void> {
    const prompt = (revisionPrompts[plan.id] || plan.teacherPrompt).trim();
    if (!prompt) return;
    setWorking(plan.id); setError(null);
    try { await regenerateLiveCheckpoint(sessionId, plan.id, prompt); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tạo lại checkpoint."); await load(); }
    finally { setWorking(null); }
  }

  useEffect(() => {
    if (!session || session.status === "draft" || openPlan || generatingPlan || previewPlan || !session.nextTranscriptRef) return;
    const timer = window.setTimeout(async () => {
      try {
        await updateLiveState(sessionId, { currentSlide: session.currentSlide || 1, currentTranscriptRef: session.nextTranscriptRef as string });
        await load();
      } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể cập nhật transcript trực tiếp."); }
    }, 650);
    return () => window.clearTimeout(timer);
  }, [generatingPlan, load, openPlan, previewPlan, session, sessionId]);

  useEffect(() => {
    if (!session || !pendingPlan || openPlan || generatingPlan || previewPlan || pendingPlan.status !== "planned") return;
    const reached = (session.currentSlide || 0) >= pendingPlan.triggerSlide && transcriptNumber(session.currentTranscriptRef) >= transcriptNumber(pendingPlan.requiredTranscriptRef);
    if (!reached) return;
    const timer = window.setTimeout(() => void generatePlan(pendingPlan), 0);
    return () => window.clearTimeout(timer);
  }, [generatePlan, generatingPlan, openPlan, pendingPlan, previewPlan, session]);

  const statusText = generatingPlan ? "Đang tạo câu hỏi từ nội dung vừa giảng..." : openPlan ? "Đang chờ phản hồi" : previewPlan ? "Đang xem trước checkpoint" : failedPlan ? "Checkpoint cần được thử lại" : "Đang nghe bài giảng";
  const transcript = session?.visibleTranscript || [];
  const slideUrl = `${API_URL}/api/teaching-agent/live-lesson/slides#page=${session?.currentSlide || 1}&view=FitH`;
  const isRecording = session?.status !== "draft" && !generatingPlan && !openPlan && !previewPlan && !failedPlan;

  return <AppLayout>
    <div className="page-heading live-heading"><div><p className="eyebrow">PHÒNG DẠY TRỰC TIẾP</p><h1>{session?.lesson.title || "Đang tải bài giảng"}</h1><p className="muted">Transcript chỉ hiện dần theo nhịp giảng và checkpoint dùng đúng phần nội dung đã xuất hiện.</p></div>{session?.roomCode && <div className="live-room-code"><span>Mã phòng</span><strong>{session.roomCode}</strong></div>}</div>
    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {loading ? <Spin tip="Đang tải phòng học..." /> : session && <div className="live-classroom-grid">
      <section className="teacher-stage"><Card className="live-stage-card">
        <div className="stage-topline"><Tag color={session.status === "live" ? "red" : session.status === "ready" ? "green" : "blue"}>{session.status === "draft" ? "Bản nháp" : session.status === "ready" ? "Sẵn sàng" : "Đang dạy"}</Tag><span>Slide {session.currentSlide || 1} / 29</span></div>
        <h2>{currentPlan?.sectionTitle || "Đang bắt đầu bài giảng"}</h2><p className="stage-objective">{statusText}</p>
        <iframe key={session.currentSlide || 1} title={`Slide ${session.currentSlide || 1}`} src={slideUrl} style={{ width: "100%", height: 500, border: "1px solid #e5e5e5", borderRadius: 12, margin: "12px 0" }} />
        <div className="stage-controls">{session.status === "draft" ? <Button type="primary" size="large" loading={working === "start"} onClick={() => void startClassroom()}>Bắt đầu lớp học</Button> : <Button type="primary" size="large" disabled={Boolean(openPlan || generatingPlan || previewPlan) || (session.currentSlide || 1) >= 29} loading={working === "slide"} onClick={() => void advanceSlide()}>Slide tiếp theo</Button>}</div>
        {currentPlan && <Card size="small" title="Checkpoint hiện tại"><p><strong>Trigger slide {currentPlan.triggerSlide}</strong></p><p className="muted">Yêu cầu ban đầu: {currentPlan.teacherPrompt}</p>{currentPlan.status === "preview" && <><div className="checkpoint-preview-list">{previewQuestions.map((question, index) => <Card key={question.id} size="small" title={`Câu hỏi ${index + 1}`}><p><strong>{question.question}</strong></p>{question.options.map(option => <p key={option.id}>{option.id}. {option.text}{option.correct ? " (Đáp án đúng)" : ""}</p>)}</Card>)}</div><div className="checkpoint-revision"><Input.TextArea value={revisionPrompts[currentPlan.id] ?? currentPlan.teacherPrompt} onChange={event => setRevisionPrompts(current => ({ ...current, [currentPlan.id]: event.target.value }))} autoSize={{ minRows: 2, maxRows: 4 }} maxLength={2000} placeholder="Ví dụ: đổi thành câu hỏi thực hành, khó hơn." /><div className="checkpoint-revision-actions"><Button loading={working === currentPlan.id} onClick={() => void regeneratePlan(currentPlan)}>Tạo lại</Button><Button type="primary" loading={working === currentPlan.id} onClick={() => void openPlanToStudents(currentPlan)}>Mở checkpoint cho học viên</Button></div></div></>}{currentPlan.status === "failed" && <Button type="primary" loading={working === currentPlan.id} onClick={() => void regeneratePlan(currentPlan)}>Thử tạo lại câu hỏi</Button>}{currentPlan.status === "open" && <Button danger loading={working === currentPlan.id} onClick={() => void closePlan(currentPlan)}>Đóng checkpoint</Button>}</Card>}
      </Card></section>
      <aside className="live-side-panel">
        <Card className="student-join-card" title="Học viên vào lớp">
          <QRCode value={joinUrl} size={128} bordered={false} />
          <Descriptions column={1} size="small" items={[{ key: "code", label: "Mã phòng", children: <strong>{session.roomCode}</strong> }, { key: "link", label: "Trang vào lớp", children: <Link href="/join">/join</Link> }]} />
          {session.status === "draft" ? <Alert type="warning" showIcon description="Bấm Bắt đầu lớp học trước khi chia mã cho học viên." /> : <Alert type="success" showIcon description="Học viên nhập mã phòng và tên hiển thị, không cần tài khoản." />}
        </Card>
        <Card title="Live transcription"><div className="recording-status"><div className={`recording-wave${isRecording ? " is-recording" : ""}`} aria-label={isRecording ? "Đang ghi âm" : "Ghi âm đang tạm dừng"}><span /><span /><span /><span /><span /></div><Tag color={isRecording ? "green" : generatingPlan ? "gold" : "red"}>{isRecording ? "Đang ghi âm" : statusText}</Tag></div><div style={{ maxHeight: 260, overflowY: "auto", marginTop: 12 }}>{transcript.length ? transcript.slice(-8).map(item => <p key={item.ref}><strong>{item.ref}</strong> {item.text}</p>) : <p className="muted">Đang chờ lời giảng đầu tiên...</p>}</div></Card>
        <Card className="live-response-card" title="Tín hiệu lớp học">
          {summary ? <>
            <div className="response-number"><strong>{currentResult?.totalResponses ?? 0}</strong><span>phản hồi tại checkpoint</span></div>
            <p className="response-participation">{summary.respondingStudents}/{summary.expectedStudents ?? summary.joinedStudents} học viên đã trả lời · {summary.joinedStudents} đã vào phòng</p>
            <Progress percent={correctRate} strokeColor="#58cc02" trailColor="#e5e5e5" />
            <Tag color={recommendationColor[activeRecommendation]}>{recommendationText[activeRecommendation]}</Tag>
            <p className="muted">{currentResult?.reason ?? summary.reason}</p>
            {currentResult && currentResult.totalResponses > 0 && <div className="result-breakdown">
              <strong>Phân bố đáp án</strong>
              {currentResult.optionDistribution.map(option => <div className="answer-row" key={option.optionId}>
                <span>{option.optionId}. {option.text}{option.correct ? " (đúng)" : ""}</span>
                <em>{option.count} ({Math.round(option.ratio * 100)}%)</em>
              </div>)}
            </div>}
            {correctAnswer && <Alert type="success" showIcon title="Đáp án đúng sau khi đóng checkpoint" description={<strong>{correctAnswer.optionId}. {correctAnswer.text}</strong>} style={{ marginTop: 12 }} />}
            {currentResult?.dominantMisconception?.statement && <p><strong>Hiểu nhầm nổi bật:</strong> {currentResult.dominantMisconception.statement}</p>}
            {currentResult?.aiAnalysis ? <div className="ai-class-analysis">
              <div><Tag color={currentResult.aiAnalysis.generatedBy === "ai" ? "purple" : "default"}>{currentResult.aiAnalysis.generatedBy === "ai" ? "AI phân tích" : "Phân tích theo quy tắc"}</Tag></div>
              <strong>{currentResult.aiAnalysis.overview}</strong>
              <p>{currentResult.aiAnalysis.pattern}</p>
              <p><b>Gợi ý:</b> {currentResult.aiAnalysis.suggestedAction}</p>
            </div> : openPlan && currentResult && currentResult.totalResponses > 0 ? <Alert type="info" showIcon title="Đóng checkpoint để AI phân tích" description="AI chỉ nhận số liệu tổng hợp ẩn danh sau khi giảng viên chốt phản hồi." /> : null}
          </> : <p className="muted">Kết quả phản hồi sẽ xuất hiện khi học viên trả lời.</p>}
        </Card>
        <Card className="slide-list-card" title="Các checkpoint">{plans.map(plan => <div key={plan.id} style={{ marginBottom: 10 }}><strong>{plan.order}. {plan.sectionTitle}</strong><div><Tag color={plan.status === "open" ? "green" : plan.status === "preview" ? "purple" : plan.status === "failed" ? "red" : plan.status === "generating" ? "gold" : "blue"}>{plan.status}</Tag> Slide {plan.triggerSlide}</div></div>)}</Card>
      </aside>
    </div>}
  </AppLayout>;
}
