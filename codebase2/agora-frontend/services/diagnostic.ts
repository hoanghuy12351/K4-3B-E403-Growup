import { apiRequest, USE_MOCK } from "./api";

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
  order?: number;
  slidePages?: number[];
  triggerSlide?: number;
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
  originalSectionId?: string;
  title: string;
  order: number;
  sourceRefs: Array<{ type: string; id: string }>;
  concepts: string[];
}

export interface GeneratedQuestion {
  id: string;
  sectionId: string;
  originalSectionId?: string;
  concept: string;
  question: string;
  learningObjective?: string;
  options: DiagnosticOption[];
  sourceRefs?: Array<{ type: string; id: string }>;
}

export type TeacherPreviewQuestion = Omit<GeneratedQuestion, "options"> & {
  options: Array<DiagnosticOption & { correct: boolean }>;
};

export interface DiagnosticSession {
  sessionId: string;
  roomCode?: string;
  lesson: { title: string; sourceId: string };
  sections: DiagnosticSection[];
  questions: GeneratedQuestion[];
  status: string;
  activeQuestionId?: string | null;
  activeQuestionIds?: string[];
  createdAt: string;
  checkpointPlans?: LiveCheckpointPlan[];
  currentSlide?: number;
  currentTranscriptRef?: string | null;
  nextTranscriptRef?: string | null;
  visibleTranscript?: Array<{ ref: string; text: string }>;
  checkpointPreviews?: Array<{ planId: string; questions: TeacherPreviewQuestion[] }>;
}

export interface LiveCheckpointPlan {
  id: string;
  sectionId: string;
  sectionTitle: string;
  order: number;
  slidePages: number[];
  triggerSlide: number;
  requiredTranscriptRef: string;
  teacherPrompt: string;
  status: "planned" | "generating" | "preview" | "open" | "closed" | "failed";
  questionIds: string[];
}

export interface CreateLiveSessionRequest {
  lessonId: string;
  expectedStudents: number;
  checkpointSelections: Array<{ sectionId: string; teacherPrompt: string; triggerSlide?: number }>;
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
  generation: {
    mode: string;
    provider: string | null;
    model: string | null;
    fallbackUsed: boolean;
    interpretedRequest?: { questionCount: number; difficulty?: string | null; style?: string | null; focus?: string | null };
  };
}

export interface DiagnosticSummary {
  respondingStudents: number;
  joinedStudents: number;
  totalResponses: number;
  expectedStudents: number | null;
  recommendation: "reteach" | "clarify" | "continue" | "insufficient_data";
  reason: string;
  lecturerDecisionRequired: boolean;
  sectionResults: Array<{
    sectionId: string;
    totalResponses: number;
    correctRate: number;
    recommendation?: "reteach" | "clarify" | "continue" | "insufficient_data";
    reason?: string;
    optionDistribution: Array<{
      optionId: string;
      text: string;
      count: number;
      ratio: number;
      correct: boolean;
      misconception?: string | null;
    }>;
    aiAnalysis: {
      overview: string;
      pattern: string;
      suggestedAction: string;
      generatedBy: "ai" | "rules";
    } | null;
    dominantMisconception: { statement?: string } | null;
  }>;
}

type MockResponse = { participantId: string; questionId: string; sectionId: string; optionId: string; explanation?: string };
type MockSession = DiagnosticSession & {
  expectedStudents: number;
  participants: Record<string, string>;
  responses: MockResponse[];
  correctOptions: Record<string, string>;
};

const MOCK_SESSIONS_KEY = "growup-mock-diagnostic-sessions-v1";

const mockCatalog: PresetDemoCatalog = {
  lesson: { id: "mock-ai-lesson", title: "AI & LLM Foundation" },
  agentMessage: "Em đã phân tích bài giảng mockup thành các phần lớn để thầy/cô chọn checkpoint.",
  mode: "preset_demo",
  sections: [
    {
      id: "ai-landscape",
      title: "Bức tranh AI và các tầng năng lực",
      concepts: ["AI", "Machine Learning", "Generative AI"],
      learningObjectives: ["Phân biệt AI, Machine Learning và Generative AI qua ví dụ thực tế."],
      misconceptions: [{ id: "mix-ai-ml", statement: "Nhầm AI với Machine Learning hoặc Generative AI." }],
    },
    {
      id: "training-inference",
      title: "Training và inference",
      concepts: ["Training", "Inference", "Dữ liệu huấn luyện"],
      learningObjectives: ["Giải thích mô hình học từ dữ liệu và dùng mô hình để dự đoán."],
      misconceptions: [{ id: "training-equals-use", statement: "Cho rằng training và inference là cùng một bước." }],
    },
    {
      id: "limits-risk",
      title: "Giới hạn và rủi ro của mô hình",
      concepts: ["Hallucination", "Thiếu dữ liệu", "Kiểm chứng kết quả"],
      learningObjectives: ["Nhận biết khi nào không nên tin hoàn toàn vào câu trả lời của AI."],
      misconceptions: [{ id: "ai-always-right", statement: "Tin rằng AI luôn trả lời đúng nếu diễn đạt tự tin." }],
    },
  ],
};

const mockQuestionBank: Record<string, Array<{ concept: string; question: string; correctOptionId: string; options: DiagnosticOption[] }>> = {
  "ai-landscape": [
    { concept: "AI", question: "Ví dụ nào mô tả đúng nhất một hệ thống AI?", correctOptionId: "B", options: [
      { id: "A", text: "Một file Excel có công thức cộng điểm." },
      { id: "B", text: "Một hệ thống nhận diện ảnh mèo/chó từ dữ liệu đã học." },
      { id: "C", text: "Một website tĩnh chỉ hiển thị nội dung cố định." },
      { id: "D", text: "Một máy tính bỏ túi thực hiện phép cộng." },
    ] },
    { concept: "Machine Learning", question: "Điểm khác chính của Machine Learning so với lập trình luật cố định là gì?", correctOptionId: "C", options: [
      { id: "A", text: "Không cần dữ liệu." },
      { id: "B", text: "Luôn đúng 100%." },
      { id: "C", text: "Mô hình học quy luật từ dữ liệu mẫu." },
      { id: "D", text: "Chỉ dùng được cho văn bản." },
    ] },
    { concept: "Generative AI", question: "Generative AI thường tạo ra loại đầu ra nào?", correctOptionId: "A", options: [
      { id: "A", text: "Văn bản, ảnh, âm thanh hoặc mã mới dựa trên mẫu đã học." },
      { id: "B", text: "Chỉ lưu trữ dữ liệu trong bảng." },
      { id: "C", text: "Chỉ kiểm tra lỗi chính tả." },
      { id: "D", text: "Chỉ chạy phép tính số học." },
    ] },
  ],
  "training-inference": [
    { concept: "Training", question: "Trong bước training, mô hình chủ yếu làm gì?", correctOptionId: "B", options: [
      { id: "A", text: "Trả lời câu hỏi của người dùng cuối." },
      { id: "B", text: "Điều chỉnh tham số dựa trên dữ liệu huấn luyện." },
      { id: "C", text: "Xóa toàn bộ dữ liệu đầu vào." },
      { id: "D", text: "Chỉ hiển thị giao diện web." },
    ] },
    { concept: "Inference", question: "Inference xảy ra khi nào?", correctOptionId: "D", options: [
      { id: "A", text: "Khi nhóm thu thập dữ liệu lần đầu." },
      { id: "B", text: "Khi mô hình chưa có tham số." },
      { id: "C", text: "Khi xóa mô hình khỏi hệ thống." },
      { id: "D", text: "Khi dùng mô hình đã học để tạo dự đoán/câu trả lời." },
    ] },
    { concept: "Dữ liệu", question: "Vì sao dữ liệu huấn luyện kém có thể làm mô hình trả lời kém?", correctOptionId: "C", options: [
      { id: "A", text: "Vì mô hình không dùng dữ liệu." },
      { id: "B", text: "Vì dữ liệu chỉ ảnh hưởng giao diện." },
      { id: "C", text: "Vì mô hình học quy luật từ dữ liệu đó." },
      { id: "D", text: "Vì inference luôn tự sửa mọi lỗi dữ liệu." },
    ] },
  ],
  "limits-risk": [
    { concept: "Hallucination", question: "Hallucination trong LLM nghĩa là gì?", correctOptionId: "A", options: [
      { id: "A", text: "Mô hình tạo câu trả lời nghe hợp lý nhưng có thể sai." },
      { id: "B", text: "Mô hình chạy nhanh hơn bình thường." },
      { id: "C", text: "Mô hình không cần kiểm chứng." },
      { id: "D", text: "Mô hình chỉ trả lời bằng hình ảnh." },
    ] },
    { concept: "Kiểm chứng", question: "Khi dùng AI cho nội dung quan trọng, thao tác nào cần làm?", correctOptionId: "D", options: [
      { id: "A", text: "Tin ngay nếu câu trả lời dài." },
      { id: "B", text: "Bỏ qua nguồn dữ liệu." },
      { id: "C", text: "Chỉ nhìn vào giọng văn tự tin." },
      { id: "D", text: "Kiểm chứng bằng tài liệu hoặc nguồn đáng tin cậy." },
    ] },
    { concept: "Thiếu dữ liệu", question: "Khi rất ít học viên trả lời checkpoint, hệ thống nên kết luận thế nào?", correctOptionId: "B", options: [
      { id: "A", text: "Cả lớp chắc chắn đã hiểu." },
      { id: "B", text: "Chưa đủ dữ liệu để kết luận cho cả lớp." },
      { id: "C", text: "Tất cả học viên đều sai." },
      { id: "D", text: "Không cần hỏi thêm." },
    ] },
  ],
};

function readMockSessions(): Record<string, MockSession> {
  if (typeof window === "undefined") return {};
  const raw = localStorage.getItem(MOCK_SESSIONS_KEY);
  if (!raw) return {};
  try { return JSON.parse(raw) as Record<string, MockSession>; }
  catch { return {}; }
}

function writeMockSessions(sessions: Record<string, MockSession>): void {
  localStorage.setItem(MOCK_SESSIONS_KEY, JSON.stringify(sessions));
}

function saveMockSession(session: MockSession): MockSession {
  const sessions = readMockSessions();
  sessions[session.sessionId] = session;
  writeMockSessions(sessions);
  return session;
}

function findMockSessionByRoom(roomCode: string): MockSession {
  const session = Object.values(readMockSessions()).find(item => item.roomCode?.toUpperCase() === roomCode.trim().toUpperCase());
  if (!session) throw new Error("Không tìm thấy mã phòng mockup.");
  return session;
}

function getMockSession(sessionId: string): MockSession {
  const session = readMockSessions()[sessionId];
  if (!session) throw new Error("Không tìm thấy bài giảng mockup.");
  return session;
}

function createRoomCode(): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let suffix = "";
  for (let index = 0; index < 5; index += 1) suffix += alphabet[Math.floor(Math.random() * alphabet.length)];
  return suffix;
}

function buildMockSession(sectionId: string, expectedStudents: number): MockSession {
  const selected = mockCatalog.sections.find(section => section.id === sectionId) ?? mockCatalog.sections[0];
  const bank = mockQuestionBank[selected.id] ?? mockQuestionBank["ai-landscape"];
  const sessionId = `mock-${Date.now()}`;
  const sections: DiagnosticSection[] = bank.map((item, index) => ({
    id: `${selected.id}-${index + 1}`,
    originalSectionId: selected.id,
    title: `${selected.title} · Câu ${index + 1}`,
    order: index + 1,
    sourceRefs: [{ type: "slide", id: `slide-${index + 1}` }],
    concepts: [item.concept],
  }));
  const questions: GeneratedQuestion[] = bank.map((item, index) => ({
    id: `${sessionId}-q${index + 1}`,
    sectionId: sections[index].id,
    originalSectionId: selected.id,
    concept: item.concept,
    question: item.question,
    learningObjective: selected.learningObjectives[0],
    options: item.options,
    sourceRefs: sections[index].sourceRefs,
  }));
  return saveMockSession({
    sessionId,
    roomCode: createRoomCode(),
    lesson: { title: mockCatalog.lesson.title, sourceId: mockCatalog.lesson.id },
    sections,
    questions,
    status: "draft",
    activeQuestionId: null,
    activeQuestionIds: [],
    createdAt: new Date().toISOString(),
    expectedStudents,
    participants: {},
    responses: [],
    correctOptions: Object.fromEntries(questions.map((question, index) => [question.id, bank[index].correctOptionId])),
  });
}

function buildMockSummary(session: MockSession): DiagnosticSummary {
  const participantIds = new Set(session.responses.map(response => response.participantId));
  const sectionResults = session.sections.map(section => {
    const question = session.questions.find(item => item.sectionId === section.id);
    const responses = question ? session.responses.filter(response => response.questionId === question.id) : [];
    const correct = question ? responses.filter(response => response.optionId === session.correctOptions[question.id]).length : 0;
    return {
      sectionId: section.id,
      totalResponses: responses.length,
      correctRate: responses.length ? correct / responses.length : 0,
      optionDistribution: question?.options.map(option => {
        const count = responses.filter(response => response.optionId === option.id).length;
        return { optionId: option.id, text: option.text, count, ratio: responses.length ? count / responses.length : 0, correct: option.id === session.correctOptions[question.id] };
      }) ?? [],
      aiAnalysis: null,
      dominantMisconception: responses.length && correct / responses.length < 0.6 ? { statement: "Nhiều học viên chọn sai ở cùng một khái niệm." } : null,
    };
  });
  const totalResponses = sectionResults.reduce((sum, item) => sum + item.totalResponses, 0);
  const averageCorrect = sectionResults.length ? sectionResults.reduce((sum, item) => sum + item.correctRate, 0) / sectionResults.length : 0;
  const coverage = session.expectedStudents ? participantIds.size / session.expectedStudents : 0;
  const recommendation = totalResponses < 5 || coverage < 0.3 ? "insufficient_data" : averageCorrect < 0.55 ? "reteach" : averageCorrect < 0.75 ? "clarify" : "continue";
  const reason = recommendation === "insufficient_data"
    ? "Chưa đủ phản hồi để kết luận cho cả lớp."
    : recommendation === "reteach"
      ? "Tỉ lệ đúng còn thấp, nên giảng lại phần này trước khi đi tiếp."
      : recommendation === "clarify"
        ? "Lớp có tín hiệu hiểu một phần, nên làm rõ thêm một vài ý."
        : "Phần lớn phản hồi đúng, có thể tiếp tục bài học.";
  return { respondingStudents: participantIds.size, joinedStudents: Object.keys(session.participants).length, totalResponses, expectedStudents: session.expectedStudents, recommendation, reason, lecturerDecisionRequired: true, sectionResults };
}

export async function joinRoom(roomCode: string, displayName: string): Promise<RoomJoinResult> {
  if (USE_MOCK) {
    const session = findMockSessionByRoom(roomCode);
    if (!['ready', 'live'].includes(session.status)) throw new Error("Giảng viên chưa tạo lớp học.");
    const participantId = `anon-${Date.now()}-${Math.round(Math.random() * 999)}`;
    session.participants[participantId] = displayName.trim();
    saveMockSession(session);
    return { participantId, sessionId: session.sessionId, roomCode: session.roomCode ?? roomCode };
  }
  return apiRequest<RoomJoinResult>("/api/diagnostic-sessions/rooms/join", {
    method: "POST",
    body: JSON.stringify({ roomCode, displayName }),
  });
}

export async function getRoomState(roomCode: string, participantId: string): Promise<{ activeQuestion: ActiveQuestion | null; activeQuestions: ActiveQuestion[] }> {
  if (USE_MOCK) {
    const session = findMockSessionByRoom(roomCode);
    if (!session.participants[participantId]) throw new Error("Bạn chưa vào phòng học này.");
    const activeQuestions = session.questions.filter(question => session.activeQuestionIds?.includes(question.id)).map(question => ({ id: question.id, sectionId: question.sectionId, question: question.question, options: question.options }));
    return { activeQuestion: activeQuestions[0] ?? null, activeQuestions };
  }
  return apiRequest(`/api/diagnostic-sessions/rooms/${encodeURIComponent(roomCode)}/state?participantId=${encodeURIComponent(participantId)}`);
}

export async function listLessonMaterials(): Promise<LessonMaterial[]> {
  if (USE_MOCK) return [{ id: mockCatalog.lesson.id, title: mockCatalog.lesson.title, description: "Bài giảng mockup có sẵn." }];
  const response = await apiRequest<{ materials: LessonMaterial[] }>("/api/diagnostic-sessions/lesson-materials");
  return response.materials;
}

export async function uploadLessonMaterial(file: File, title?: string): Promise<LessonMaterial> {
  if (USE_MOCK) return { id: `mock-upload-${Date.now()}`, title: title?.trim() || file.name, description: "Tài liệu mockup." };
  const body = new FormData();
  body.append("file", file);
  if (title?.trim()) body.append("title", title.trim());
  return apiRequest<LessonMaterial>("/api/lesson-materials", { method: "POST", body });
}

export async function createDiagnosticSession(materialId: string, expectedStudents: number): Promise<{ sessionId: string }> {
  if (USE_MOCK) return { sessionId: buildMockSession(materialId, expectedStudents).sessionId };
  return apiRequest<{ sessionId: string }>("/api/diagnostic-sessions", {
    method: "POST",
    body: JSON.stringify({ lesson: { materialId }, expectedStudents }),
  });
}

export async function getPresetDemoCatalog(): Promise<PresetDemoCatalog> {
  if (USE_MOCK) return mockCatalog;
  return apiRequest<PresetDemoCatalog>("/api/teaching-agent/demo");
}

export async function createLiveSession(request: CreateLiveSessionRequest): Promise<{ sessionId: string; roomCode: string; status: string; checkpointPlans: LiveCheckpointPlan[] }> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp cần NEXT_PUBLIC_USE_MOCK=false và backend có LLM được cấu hình.");
  return apiRequest("/api/teaching-agent/live-session", { method: "POST", body: JSON.stringify(request) });
}

export async function createPresetDemoCheckpoint(sectionId: string, expectedStudents: number): Promise<{ sessionId: string }> {
  if (USE_MOCK) return { sessionId: buildMockSession(sectionId, expectedStudents).sessionId };
  return apiRequest<{ sessionId: string }>("/api/teaching-agent/demo/checkpoints", {
    method: "POST",
    body: JSON.stringify({ sectionId, expectedStudents }),
  });
}

export async function generateAgentCheckpoints(request: AgentGenerateRequest): Promise<AgentGeneratedSession> {
  if (USE_MOCK) {
    const session = buildMockSession(request.sectionId, request.expectedStudents);
    const selected = mockCatalog.sections.find(section => section.id === request.sectionId) ?? mockCatalog.sections[0];
    return {
      agentMessage: `Em đã tạo ${session.questions.length} câu hỏi mockup cho phần ${selected.title}.`,
      sessionId: session.sessionId,
      roomCode: session.roomCode ?? "",
      status: session.status,
      selectedSection: { id: selected.id, title: selected.title },
      teacherRequest: request.teacherRequest,
      checkpoints: session.questions,
      generation: { mode: "mockup", provider: null, model: null, fallbackUsed: true, interpretedRequest: { questionCount: session.questions.length, difficulty: "medium", style: "demo", focus: "concept_check" } },
    };
  }
  return apiRequest<AgentGeneratedSession>("/api/teaching-agent/demo/generate", {
    method: "POST",
    timeoutMs: 90000,
    body: JSON.stringify(request),
  });
}

export async function getDiagnosticSession(sessionId: string): Promise<DiagnosticSession> {
  if (USE_MOCK) return getMockSession(sessionId);
  return apiRequest<DiagnosticSession>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}`);
}

export async function updateLiveState(sessionId: string, state: { currentSlide: number; currentTranscriptRef: string }): Promise<void> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp không hỗ trợ mock mode.");
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/live-state`, { method: "POST", body: JSON.stringify(state) });
}

export async function triggerLiveCheckpoint(sessionId: string, planId: string): Promise<void> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp không hỗ trợ mock mode.");
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/${encodeURIComponent(planId)}/trigger`, { method: "POST", timeoutMs: 90000 });
}

export async function openLiveCheckpoint(sessionId: string, planId: string): Promise<void> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp không hỗ trợ mock mode.");
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/${encodeURIComponent(planId)}/open`, { method: "POST" });
}

export async function regenerateLiveCheckpoint(sessionId: string, planId: string, teacherPrompt: string): Promise<void> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp không hỗ trợ mock mode.");
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/${encodeURIComponent(planId)}/regenerate`, { method: "POST", timeoutMs: 90000, body: JSON.stringify({ teacherPrompt }) });
}

export async function closeLiveCheckpoint(sessionId: string, planId: string): Promise<void> {
  if (USE_MOCK) throw new Error("Luồng lớp học trực tiếp không hỗ trợ mock mode.");
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/${encodeURIComponent(planId)}/close`, { method: "POST" });
}

export async function startDiagnosticSession(sessionId: string): Promise<{ sessionId: string; roomCode: string; status: string }> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.status = "ready";
    saveMockSession(session);
    return { sessionId: session.sessionId, roomCode: session.roomCode ?? "", status: session.status };
  }
  return apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/start`, { method: "POST" });
}

export async function openCheckpoint(sessionId: string, questionId: string): Promise<void> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.status = "live";
    session.activeQuestionId = questionId;
    session.activeQuestionIds = [questionId];
    saveMockSession(session);
    return;
  }
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoint/${encodeURIComponent(questionId)}/open`, { method: "POST" });
}

export async function closeCheckpoint(sessionId: string, questionId: string): Promise<void> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.activeQuestionIds = session.activeQuestionIds?.filter(id => id !== questionId) ?? [];
    session.activeQuestionId = session.activeQuestionIds[0] ?? null;
    saveMockSession(session);
    return;
  }
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoint/${encodeURIComponent(questionId)}/close`, { method: "POST" });
}

export async function openAllCheckpoints(sessionId: string): Promise<void> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.status = "live";
    session.activeQuestionIds = session.questions.map(question => question.id);
    session.activeQuestionId = session.activeQuestionIds[0] ?? null;
    saveMockSession(session);
    return;
  }
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/open-all`, { method: "POST" });
}

export async function closeAllCheckpoints(sessionId: string): Promise<void> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.activeQuestionId = null;
    session.activeQuestionIds = [];
    saveMockSession(session);
    return;
  }
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/checkpoints/close-all`, { method: "POST" });
}

export async function submitStudentResponse(sessionId: string, request: { participantId: string; questionId: string; sectionId: string; optionId: string; explanation?: string }): Promise<void> {
  if (USE_MOCK) {
    const session = getMockSession(sessionId);
    session.responses = session.responses.filter(response => !(response.participantId === request.participantId && response.questionId === request.questionId));
    session.responses.push(request);
    saveMockSession(session);
    return;
  }
  await apiRequest(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/responses`, { method: "POST", body: JSON.stringify(request) });
}

export async function getDiagnosticSummary(sessionId: string): Promise<DiagnosticSummary> {
  if (USE_MOCK) return buildMockSummary(getMockSession(sessionId));
  return apiRequest<DiagnosticSummary>(`/api/diagnostic-sessions/${encodeURIComponent(sessionId)}/summary`);
}
