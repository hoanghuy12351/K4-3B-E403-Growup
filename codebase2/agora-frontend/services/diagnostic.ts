import { apiRequest } from "./api";

export interface LessonMaterial {
  id: string;
  title: string;
  description?: string;
}

export interface PresetDemoSection {
  id: string;
  title: string;
  concepts: string[];
  learningObjectives: string[];
  misconceptions: Array<{ id: string; statement: string }>;
}

export interface PresetDemoCatalog {
  lesson: { id: string; title: string };
  agentMessage: string;
  sections: PresetDemoSection[];
  mode: "preset_demo";
}

export interface DiagnosticOption {
  id: string;
  text: string;
}

export interface DiagnosticSection {
  id: string;
  title: string;
  order: number;
  sourceRefs: Array<{ type: string; id: string }>;
  concepts: string[];
}

export interface GeneratedQuestion {
  id: string;
  sectionId: string;
  concept: string;
  question: string;
  learningObjective?: string;
  options: DiagnosticOption[];
  sourceRefs?: Array<{ type: string; id: string }>;
}

export interface DiagnosticSession {
  sessionId: string;
  roomCode?: string;
  lesson: { title: string; sourceId: string };
  sections: DiagnosticSection[];
  questions: GeneratedQuestion[];
  status: string;
  activeQuestionId?: string | null;
  createdAt: string;
}

export interface RoomJoinResult {
  participantId: string;
  sessionId: string;
  roomCode: string;
}

export interface ActiveQuestion {
  id: string;
  sectionId: string;
  question: string;
  options: Array<{ id: string; text: string }>;
}

export interface AgentGenerateRequest {
  sectionId: string;
  teacherRequest: string;
  questionCount: number;
  expectedStudents: number;
}

export interface AgentGeneratedSession {
  agentMessage: string;
  sessionId: string;
  roomCode: string;
  status: string;
  selectedSection: { id: string; title: string };
  teacherRequest: string;
  checkpoints: GeneratedQuestion[];
  generation: { mode: string; provider: string | null; model: string | null; fallbackUsed: boolean };
}

export interface DiagnosticSummary {
  respondingStudents: number;
  expectedStudents: number | null;
  recommendation: "reteach" | "clarify" | "continue" | "insufficient_data";
  reason: string;
  lecturerDecisionRequired: boolean;
  sectionResults: Array<{
    sectionId: string;
    totalResponses: number;
    correctRate: number;
    dominantMisconception: { statement?: string } | null;
  }>;
}

export async function joinRoom(roomCode: string, displayName: string): Promise<RoomJoinResult> {
  return apiRequest<RoomJoinResult>("/api/diagnostic-sessions/rooms/join", {
    method: "POST",
    body: JSON.stringify({ roomCode, displayName }),
  });
}

export async function getRoomState(roomCode: string, participantId: string): Promise<{ activeQuestion: ActiveQuestion | null }> {
  return apiRequest(`/api/diagnostic-sessions/rooms/${encodeURIComponent(roomCode)}/state?participantId=${encodeURIComponent(participantId)}`);
}

export async function listLessonMaterials(): Promise<LessonMaterial[]> {
  const response = await apiRequest<{ materials: LessonMaterial[] }>("/api/diagnostic-sessions/lesson-materials");
  return response.materials;
}

export async function uploadLessonMaterial(file: File, title?: string): Promise<LessonMaterial> {
  const body = new FormData();
  body.append("file", file);
  if (title?.trim()) body.append("title", title.trim());
  return apiRequest<LessonMaterial>("/api/lesson-materials", { method: "POST", body });
}

export async function createDiagnosticSession(materialId: string, expectedStudents: number): Promise<{ sessionId: string }> {
  return apiRequest<{ sessionId: string }>("/api/diagnostic-sessions", {
    method: "POST",
    body: JSON.stringify({ lesson: { materialId }, expectedStudents }),
  });
}

export async function getPresetDemoCatalog(): Promise<PresetDemoCatalog> {
  return apiRequest<PresetDemoCatalog>("/api/teaching-agent/demo");
}

export async function createPresetDemoCheckpoint(sectionId: string, expectedStudents: number): Promise<{ sessionId: string }> {
  return apiRequest<{ sessionId: string }>("/api/teaching-agent/demo/checkpoints", {
    method: "POST",
    body: JSON.stringify({ sectionId, expectedStudents }),
  });
}

export async function generateAgentCheckpoints(request: AgentGenerateRequest): Promise<AgentGeneratedSession> {
  return apiRequest<AgentGeneratedSession>("/api/teaching-agent/demo/generate", {
    method: "POST",
    timeoutMs: 60000,
    body: JSON.stringify(request),
  });
}

export async function getDiagnosticSession(sessionId: string): Promise<DiagnosticSession> {
  return apiRequest<DiagnosticSession>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}`);
}

export async function startDiagnosticSession(sessionId: string): Promise<{ sessionId: string; roomCode: string; status: string }> {
  return apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/start`, { method: "POST" });
}

export async function openCheckpoint(sessionId: string, questionId: string): Promise<void> {
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoint/${encodeURIComponent(questionId)}/open`, { method: "POST" });
}

export async function closeCheckpoint(sessionId: string, questionId: string): Promise<void> {
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoint/${encodeURIComponent(questionId)}/close`, { method: "POST" });
}

export async function submitStudentResponse(sessionId: string, request: { participantId: string; questionId: string; sectionId: string; optionId: string; explanation?: string }): Promise<void> {
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/responses`, { method: "POST", body: JSON.stringify(request) });
}

export async function getDiagnosticSummary(sessionId: string): Promise<DiagnosticSummary> {
  return apiRequest<DiagnosticSummary>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/summary`);
}
