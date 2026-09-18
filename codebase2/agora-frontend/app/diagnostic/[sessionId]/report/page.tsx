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

export default function DiagnosticReportPage() {
  const params = useParams<{ sessionId: string }>();
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getDiagnosticSummary(params.sessionId).then((value) => { if (active) setSummary(value); }).catch((caught: unknown) => {
      if (active) setError(caught instanceof Error ? caught.message : "Không thể tải báo cáo.");
    });
    return () => { active = false; };
  }, [params.sessionId]);

  if (error) return <AppLayout><Alert type="error" showIcon title={error} /></AppLayout>;
  if (!summary) return <AppLayout><div className="diagnostic-loading"><Spin /> Đang tổng hợp phản hồi...</div></AppLayout>;
  return <AppLayout>
    <div className="page-heading"><div><p className="eyebrow">LECTURER REPORT</p><h1>Báo cáo mức độ hiểu</h1><p className="muted">{summary.respondingStudents} / {summary.expectedStudents ?? "?"} học viên đã phản hồi.</p></div><Tag color="purple">{summary.overallStatus}</Tag></div>
    <Alert className="diagnostic-alert" type={summary.recommendation === "reteach" ? "warning" : "info"} showIcon title={`Gợi ý: ${recommendationText[summary.recommendation]}`} description={`${summary.reason} Giảng viên là người quyết định hành động cuối cùng.`} />
    <List grid={{ gutter: 18, xs: 1, md: 2, lg: 3 }} dataSource={summary.sectionResults} renderItem={(result) => <List.Item><Card title={result.concept} extra={<Tag color={result.status === "understood" ? "green" : result.status === "uncertain" ? "gold" : "red"}>{result.status}</Tag>}>
      <h2>{Math.round(result.correctRate * 100)}%</h2><p className="muted">{result.totalResponses} phản hồi · Coverage {result.responseCoverage === null ? "không xác định" : `${Math.round(result.responseCoverage * 100)}%`}</p>
      <p>{result.reason}</p>
      {result.misconceptionSignals.map((signal) => <p key={signal.misconceptionId} className="muted">{Math.round(signal.ratio * 100)}% chọn: {signal.statement || signal.misconceptionId}</p>)}
    </Card></List.Item>} />
  </AppLayout>;
}
