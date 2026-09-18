import { apiRequest } from "./api";

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
