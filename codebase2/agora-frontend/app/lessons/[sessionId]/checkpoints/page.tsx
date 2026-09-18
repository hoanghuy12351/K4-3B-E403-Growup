"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Button, Card, Descriptions, Progress, QRCode, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { closeAllCheckpoints, closeCheckpoint, getDiagnosticSession, getDiagnosticSummary, openCheckpoint, startDiagnosticSession, type DiagnosticSession, type DiagnosticSummary } from "@/services/diagnostic";

const recommendationText = {
  reteach: "Nên giảng lại ngắn phần này trước khi chuyển tiếp.",
  clarify: "Nên làm rõ thêm một vài ý trước khi tiếp tục.",
  continue: "Lớp đang theo kịp, có thể tiếp tục bài học.",
  insufficient_data: "Chưa đủ phản hồi để kết luận.",
};

const recommendationColor = {
  reteach: "red",
  clarify: "orange",
  continue: "green",
  insufficient_data: "blue",
} as const;

export default function LiveTeachingPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    try {
      const next = await getDiagnosticSession(sessionId);
      setSession(next);
      if (next.status !== "draft") setSummary(await getDiagnosticSummary(sessionId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải phòng học.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => {
    if (!session || session.status === "draft") return;
    const timer = window.setInterval(() => void load(), 2000);
    return () => window.clearInterval(timer);
  }, [session, load]);

  const currentSection = session?.sections[currentIndex];
  const currentQuestion = currentSection ? session?.questions.find(item => item.sectionId === currentSection.id) : undefined;
  const activeQuestionIds = session?.activeQuestionIds ?? [];
  const currentQuestionOpen = Boolean(currentQuestion && activeQuestionIds.includes(currentQuestion.id));
  const currentResult = currentSection ? summary?.sectionResults.find(item => item.sectionId === currentSection.id) : undefined;
  const correctRate = Math.round((currentResult?.correctRate ?? 0) * 100);
  const activeRecommendation = currentResult?.recommendation ?? summary?.recommendation ?? "insufficient_data";
  const joinUrl = typeof window === "undefined" ? "/join" : `${window.location.origin}/join`;

  const answeredCount = useMemo(() => summary?.respondingStudents ?? 0, [summary]);

  async function startClassroom(): Promise<void> {
    setWorking("start"); setError(null);
    try { await startDiagnosticSession(sessionId); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tạo lớp học."); } finally { setWorking(null); }
  }

  async function openCurrentQuestion(): Promise<void> {
    if (!currentQuestion) return;
    setWorking(currentQuestion.id); setError(null);
    try { await openCheckpoint(sessionId, currentQuestion.id); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể mở câu hỏi."); } finally { setWorking(null); }
  }

  async function closeCurrentQuestion(): Promise<void> {
    if (!currentQuestion) return;
    setWorking(currentQuestion.id); setError(null);
    try { await closeCheckpoint(sessionId, currentQuestion.id); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể đóng câu hỏi."); } finally { setWorking(null); }
  }

  async function closeQuestions(): Promise<void> {
    setWorking("close-all"); setError(null);
    try { await closeAllCheckpoints(sessionId); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể đóng câu hỏi."); } finally { setWorking(null); }
  }

  function goToSlide(index: number): void {
    if (!session) return;
    setCurrentIndex(Math.min(Math.max(index, 0), session.sections.length - 1));
  }

  return <AppLayout>
    <div className="page-heading live-heading"><div><p className="eyebrow">PHÒNG DẠY TRỰC TIẾP</p><h1>{session?.lesson.title || "Đang tải bài giảng"}</h1><p className="muted">Giảng viên điều khiển nhịp trình chiếu, học viên vào bằng mã phòng và chỉ thấy câu hỏi khi bạn mở.</p></div>
      {session?.roomCode && <div className="live-room-code"><span>Mã phòng</span><strong>{session.roomCode}</strong></div>}
    </div>

    {error && <Alert type="error" showIcon title="Không thể hoàn tất yêu cầu" description={error} style={{ marginBottom: 16 }} />}
    {loading ? <Spin tip="Đang tải phòng học..." /> : session && currentSection && currentQuestion && <div className="live-classroom-grid">
      <section className="teacher-stage">
        <Card className="live-stage-card">
          <div className="stage-topline"><Tag color={session.status === "live" ? "red" : session.status === "ready" ? "green" : "blue"}>{session.status === "draft" ? "Bản nháp" : session.status === "ready" ? "Đã tạo lớp" : "Đang dạy"}</Tag><span>Phần {currentIndex + 1}/{session.sections.length}</span></div>
          <h2>{currentSection.title}</h2>
          <p className="stage-objective">Checkpoint này kiểm tra các ý chính trước khi giảng viên chuyển sang phần tiếp theo.</p>
          <div className="stage-concepts">{currentSection.concepts.map(concept => <span key={concept}>🎯 {concept}</span>)}</div>
          <div className="stage-question">
            <p className="eyebrow">CÂU HỎI SẼ HIỆN CHO HỌC VIÊN</p>
            <h3>{currentQuestion.question}</h3>
            <div className="question-option-list">{currentQuestion.options.map(option => <div key={option.id}>{option.id}. {option.text}</div>)}</div>
          </div>
        </Card>

        <div className="stage-controls">
          <Button size="large" disabled={currentIndex === 0} onClick={() => goToSlide(currentIndex - 1)}>← Phần trước</Button>
          {session.status === "draft" ? <Button type="primary" size="large" loading={working === "start"} onClick={() => void startClassroom()}>Tạo lớp học</Button>
            : currentQuestionOpen ? <Button danger size="large" loading={working === currentQuestion.id} onClick={() => void closeCurrentQuestion()}>Đóng câu hỏi</Button>
              : <Button type="primary" size="large" loading={working === currentQuestion.id} onClick={() => void openCurrentQuestion()}>Mở câu hỏi cho học viên</Button>}
          <Button size="large" disabled={currentIndex >= session.sections.length - 1} onClick={() => goToSlide(currentIndex + 1)}>Phần sau →</Button>
        </div>
      </section>

      <aside className="live-side-panel">
        <Card className="student-join-card" title="Học viên vào lớp">
          <QRCode value={joinUrl} size={128} bordered={false} />
          <Descriptions column={1} size="small" items={[{ key: "code", label: "Mã phòng", children: <strong>{session.roomCode}</strong> }, { key: "link", label: "Trang vào lớp", children: <Link href="/join">/join</Link> }]} />
          {session.status === "draft" ? <Alert type="warning" showIcon description="Bấm Tạo lớp học trước khi chia mã cho học viên." /> : <Alert type="success" showIcon description="Học viên nhập mã phòng và tên hiển thị, không cần tài khoản." />}
        </Card>

        <Card className="live-response-card" title="Tín hiệu lớp học">
          {summary ? <>
            <div className="response-number"><strong>{currentResult?.totalResponses ?? 0}</strong><span>phản hồi cho câu này</span></div>
            <p className="response-participation">{answeredCount}/{summary.expectedStudents ?? summary.joinedStudents} học viên đã trả lời · {summary.joinedStudents} đã vào phòng</p>
            <Progress percent={correctRate} strokeColor="#58cc02" trailColor="#e5e5e5" />
            <Tag color={recommendationColor[activeRecommendation]}>{recommendationText[activeRecommendation]}</Tag>
            <p className="muted">{currentResult?.reason ?? summary.reason}</p>
            {currentResult && currentResult.totalResponses > 0 && <div className="result-breakdown">
              <strong>Phân bố đáp án</strong>
              {currentResult.optionDistribution.map(option => <div className="answer-row" key={option.optionId}>
                <span>{option.optionId}. {option.text}{option.correct ? " ✓" : ""}</span>
                <em>{option.count} ({Math.round(option.ratio * 100)}%)</em>
              </div>)}
            </div>}
            {currentResult?.aiAnalysis ? <div className="ai-class-analysis">
              <div><Tag color={currentResult.aiAnalysis.generatedBy === "ai" ? "purple" : "default"}>{currentResult.aiAnalysis.generatedBy === "ai" ? "AI phân tích" : "Phân tích theo quy tắc"}</Tag></div>
              <strong>{currentResult.aiAnalysis.overview}</strong>
              <p>{currentResult.aiAnalysis.pattern}</p>
              <p><b>Gợi ý:</b> {currentResult.aiAnalysis.suggestedAction}</p>
            </div> : currentQuestionOpen && currentResult && currentResult.totalResponses > 0 ? <Alert type="info" showIcon title="Đóng câu hỏi để AI phân tích" description="AI chỉ nhận số liệu tổng hợp ẩn danh sau khi giảng viên chốt phản hồi." /> : null}
            <div className="teacher-decisions"><Button>Giảng lại ngắn</Button><Button type="primary">Tiếp tục</Button></div>
          </> : <p className="muted">Sau khi học viên trả lời, hệ thống sẽ hiện tỉ lệ đúng và gợi ý cho giảng viên.</p>}
        </Card>

        <Card className="slide-list-card" title="Các phần trong buổi dạy">
          <div className="live-slide-list">{session.sections.map((section, index) => {
            const question = session.questions.find(item => item.sectionId === section.id);
            const isOpen = Boolean(question && activeQuestionIds.includes(question.id));
            return <button key={section.id} className={index === currentIndex ? "active" : ""} onClick={() => goToSlide(index)}>
              <span>{index + 1}</span><strong>{section.title}</strong>{isOpen && <em>Đang mở</em>}
            </button>;
          })}</div>
          {activeQuestionIds.length > 0 && <Button danger block loading={working === "close-all"} onClick={() => void closeQuestions()}>Đóng tất cả câu hỏi</Button>}
        </Card>
      </aside>
    </div>}
  </AppLayout>;
}

