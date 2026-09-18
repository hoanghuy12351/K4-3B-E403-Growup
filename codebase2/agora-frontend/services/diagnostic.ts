import { apiRequest } from "./api";

export type Recommendation = "continue" | "clarify" | "reteach" | "insufficient_data";

export interface SourceReference {
  type: string;
  sourceId: string;
  page: number;
}

export interface DiagnosticOption {
  id: string;
  text: string;
  misconceptionId: string | null;
  correct?: boolean;
}

export interface DiagnosticQuestion {
  id: string;
  topic: string;
  concept: string;
  question: string;
  learningObjective: string;
  sectionId?: string;
  options: DiagnosticOption[];
}

export interface StudentSession {
  sessionId: string;
  lesson: { title: string; sourceId: string };
  status: "draft" | "active";
  createdAt: string;
  sections: Array<{ id: string; title: string; order: number; sourceRefs: SourceReference[]; concepts: string[] }>;
  questions: DiagnosticQuestion[];
}

export interface CreatedSession {
  sessionId: string;
  lesson: { materialId: string | null; title: string; sourceId: string; contentMode: string; sourceBlocks: Array<{ page: number; text: string }> };
  sections: Array<{
    sectionId: string;
    section: { id: string; title: string; text: string; sourceRefs: SourceReference[]; order: number };
    concepts: string[];
    question: DiagnosticQuestion;
  }>;
  status: "draft" | "active";
  createdAt: string;
}

export interface AvailableLessonMaterial {
  id: string;
  title: string;
  sourceId: string;
  type: "pdf";
}

export interface DiagnosticSummary {
  sessionId: string;
  responseCoverage: number | null;
  respondingStudents: number;
  expectedStudents: number | null;
  overallStatus: string;
  recommendation: Recommendation;
  reason: string;
  lecturerDecisionRequired: true;
  sectionResults: Array<{
    sectionId: string;
    sectionTitle: string;
    concept: string;
    totalResponses: number;
    correctResponses: number;
    incorrectResponses: number;
    responseCoverage: number | null;
    correctRate: number;
    status: string;
    recommendation: Recommendation;
    reason: string;
    misconceptionSignals: Array<{ misconceptionId: string; count: number; ratio: number; statement: string | null }>;
  }>;
}

export function listLessonMaterials() {
  return apiRequest<{ materials: AvailableLessonMaterial[] }>("/api/diagnostic-sessions/lesson-materials");
}

export function createDiagnosticSession(payload: { lesson: { materialId?: string; title?: string; text?: string; sourceId?: string; pdfPath?: string }; expectedStudents?: number }) {
  return apiRequest<CreatedSession>("/api/diagnostic-sessions", { method: "POST", body: JSON.stringify(payload) }, 120000);
}

export function getDiagnosticSession(sessionId: string) {
  return apiRequest<StudentSession>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}`);
}

export function startDiagnosticSession(sessionId: string) {
  return apiRequest<{ sessionId: string; status: "active" }>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/start`, { method: "POST" });
}

export function submitDiagnosticResponse(sessionId: string, payload: { studentId: string; questionId: string; sectionId: string; optionId: string }) {
  return apiRequest<{ answerPolicy: string }>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/responses`, { method: "POST", body: JSON.stringify(payload) });
}

export function getDiagnosticSummary(sessionId: string) {
  return apiRequest<DiagnosticSummary>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/summary`);
}
