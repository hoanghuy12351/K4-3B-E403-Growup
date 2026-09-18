"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Card, List, Spin, Tag } from "antd";
import AppLayout from "@/components/Layout/AppLayout";
import { getDiagnosticSummary, type DiagnosticSummary } from "@/services/diagnostic";

const recommendationText = {
  continue: "Có thể tiếp tục phần bài học kế tiếp.",
  clarify: "Nên làm rõ ngắn gọn trước khi tiếp tục.",
  reteach: "Nên giảng lại ngắn gọn phần khái niệm cần chú ý.",
  insufficient_data: "Chưa đủ phản hồi để đưa ra suy luận cho cả lớp.",
};

const recommendationColor = {
  continue: "green",
  clarify: "gold",
  reteach: "red",
  insufficient_data: "default",
} as const;

export default function DiagnosticReportPage() {
  const params = useParams<{ sessionId: string }>();
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadSummary() {
      try {
        const value = await getDiagnosticSummary(params.sessionId);
        if (active) {
          setSummary(value);
          setError(null);
        }
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught.message : "Không thể tải báo cáo.");
      }
    }
    void loadSummary();
    const refreshId = window.setInterval(() => { void loadSummary(); }, 3000);
    return () => { active = false; window.clearInterval(refreshId); };
  }, [params.sessionId]);

  if (error) return <AppLayout><Alert type="error" showIcon title={error} /></AppLayout>;
  if (!summary) return <AppLayout><div className="diagnostic-loading"><Spin /> Đang tổng hợp phản hồi...</div></AppLayout>;
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">LECTURER REPORT</p><h1>Báo cáo mức độ hiểu</h1><p className="muted">{summary.respondingStudents} / {summary.expectedStudents ?? "?"} học viên đã phản hồi.</p></div><Tag color="purple">{summary.overallStatus}</Tag></div>
    {summary.respondingStudents === 1 && <Alert className="diagnostic-alert" type="info" title="Báo cáo mock đã có phản hồi đầu tiên" description="Báo cáo tự cập nhật mỗi 3 giây. Cần thêm phản hồi để đề xuất giảng dạy có ý nghĩa." />}
    <Alert className="diagnostic-alert" type={summary.recommendation === "reteach" ? "warning" : "info"} showIcon title={`Gợi ý: ${recommendationText[summary.recommendation]}`} description={`${summary.reason} Giảng viên là người quyết định hành động cuối cùng.`} />
    <List grid={{ gutter: 18, xs: 1, md: 2, lg: 3 }} dataSource={summary.sectionResults} renderItem={(result) => <List.Item><Card title={result.sectionTitle} extra={<Tag color={recommendationColor[result.recommendation]}>{result.recommendation}</Tag>}>
      <p className="muted">Khái niệm: {result.concept}</p><h2>{Math.round(result.correctRate * 100)}%</h2><p className="muted">{result.totalResponses} phản hồi ({result.correctResponses} đúng, {result.incorrectResponses} sai) · Coverage {result.responseCoverage === null ? "không xác định" : `${Math.round(result.responseCoverage * 100)}%`}</p>
      <p>{result.reason}</p>
      {result.misconceptionSignals.map((signal) => <p key={signal.misconceptionId} className="muted">{Math.round(signal.ratio * 100)}% chọn: {signal.statement || signal.misconceptionId}</p>)}
    </Card></List.Item>} />
  </AppLayout>;
}
