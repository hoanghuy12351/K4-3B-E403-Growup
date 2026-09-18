import { apiRequest } from "./api";

export interface LessonMaterial {
  id: string;
  title: string;
  description?: string;
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
}

export interface DiagnosticSession {
  sessionId: string;
  roomCode?: string;
  lesson: { title: string; sourceId: string };
  sections: DiagnosticSection[];
  questions: GeneratedQuestion[];
  status: string;
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

export async function createDiagnosticSession(materialId: string, expectedStudents: number): Promise<{ sessionId: string }> {
  return apiRequest<{ sessionId: string }>("/api/diagnostic-sessions", {
    method: "POST",
    body: JSON.stringify({ lesson: { materialId }, expectedStudents }),
  });
}

export async function getDiagnosticSession(sessionId: string): Promise<DiagnosticSession> {
  return apiRequest<DiagnosticSession>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}`);
}

export async function startDiagnosticSession(sessionId: string): Promise<{ sessionId: string; roomCode: string; status: string }> {
  return apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/start`, { method: "POST" });
}
