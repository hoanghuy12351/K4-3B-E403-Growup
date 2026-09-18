"""Tests for the offline, static Teaching Agent checkpoint demo."""

import os
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:3000"

from fastapi.testclient import TestClient  # noqa: E402

from app.ai.services.demo_checkpoint_catalog import build_demo_session_sections, list_demo_sections  # noqa: E402
from app.ai.services.demo_slide_analysis import get_preanalyzed_section  # noqa: E402
from app.ai.llm.errors import LLMProviderError  # noqa: E402
from app.ai.llm.models import ProviderResult  # noqa: E402
from app.diagnostic import service as diagnostic_service  # noqa: E402
from app.main import app  # noqa: E402


def _register_teacher(client: TestClient) -> None:
    """Register a unique teacher inside the active application lifespan."""
    response = client.post("/auth/register", json={
        "name": "Preset Demo Teacher",
        "email": f"preset-demo-{uuid4().hex}@example.com",
        "password": "secure-demo-password",
    })
    assert response.status_code == 201


def test_static_fixtures_define_all_prepared_sections() -> None:
    sections = list_demo_sections()
    assert [section["id"] for section in sections] == [
        "ai-landscape",
        "transformer-breakthrough",
        "llm-mechanics",
        "attention-context",
        "training-limitations",
        "llm-to-agent",
        "model-selection-cost",
        "api-prompt-basics",
    ]
    for section in sections:
        session_sections = build_demo_session_sections(section["id"])
        assert len(session_sections) == 3
        for session_section in session_sections:
            question = session_section["question"]
            options = question["options"]
            known_misconceptions = {item["id"] for item in session_section["misconceptions"]}
            allowed_refs = {(item["type"], item["id"]) for item in session_section["section"]["sourceRefs"]}
            assert len(options) == 4
            assert sum(option.get("correct") is True for option in options) == 1
            assert all(option["misconceptionId"] in known_misconceptions for option in options if option.get("misconceptionId"))
            assert all((item["type"], item["id"]) in allowed_refs for item in question["source"])
            assert session_section["generation"]["mode"] == "preset_demo"
            assert session_section["generation"]["provider"] is None
            assert session_section["generation"]["model"] is None


def test_preanalyzed_section_contains_only_grounding_data() -> None:
    analysis = get_preanalyzed_section("attention-context")
    assert analysis["lesson"]["title"] == "AI & LLM Foundation"
    assert analysis["concepts"] == ["attention", "context management", "context rot"]
    assert analysis["learningObjectives"]
    assert analysis["misconceptions"]
    assert analysis["allowedSourceRefs"]
    assert "question" not in analysis


def test_demo_endpoints_use_static_lookup_without_runtime_ai(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("Preset demo must not call runtime AI")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr("app.ai.llm.factory.create_provider", fail)
    monkeypatch.setattr("app.ai.pipeline.generate_diagnostic_check", fail)
    monkeypatch.setattr("app.ai.services.lesson_diagnostic_service.generate_lesson_diagnostic", fail)
    monkeypatch.setattr("app.ai.services.llm_diagnostic_service.generate_llm_diagnostic", fail)
    monkeypatch.setattr("app.ai.services.slide_evidence.load_slide_evidence", fail)
    monkeypatch.setattr("app.ai.services.transcript_ingestion.parse_transcript_file", fail)
    monkeypatch.setattr("app.ai.services.section_evidence.build_section_evidence", fail)
    monkeypatch.setattr("app.ai.services.section_checkpoint_service.generate_checkpoint_for_section", fail)
    with TestClient(app) as client:
        _register_teacher(client)
        selection = client.get("/api/teaching-agent/demo")
        assert selection.status_code == 200
        assert selection.json()["mode"] == "preset_demo"
        assert len(selection.json()["sections"]) == 8

        created = client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "attention-context", "expectedStudents": 30})
        assert created.status_code == 201
        payload = created.json()
        assert payload["status"] == "draft"
        assert payload["checkpoint"]["id"] == "Q-DEMO-ATTENTION-01"
        assert len(payload["checkpoints"]) == 3
        assert payload["generation"] == {
            "mode": "preset_demo",
            "provider": None,
            "model": None,
            "latencyMs": 0,
            "fallbackUsed": False,
            "fallbackReason": None,
            "retryCount": 0,
            "usage": None,
        }


def test_preset_session_keeps_classroom_flow_private_and_offline(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("Preset demo classification must not call a provider")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(diagnostic_service, "classify_explanation", fail)
    with TestClient(app) as client:
        _register_teacher(client)
        created = client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "attention-context"})
        assert created.status_code == 201
        payload = created.json()
        session_id = payload["sessionId"]
        room_code = payload["roomCode"]

        assert client.post(f"/api/diagnostic-sessions/{session_id}/start").status_code == 200
        joined = client.post("/api/diagnostic-sessions/rooms/join", json={"roomCode": room_code, "displayName": "Anonymous Student"})
        participant_id = joined.json()["participantId"]
        assert client.post(f"/api/diagnostic-sessions/{session_id}/checkpoint/Q-DEMO-ATTENTION-01/open").status_code == 200
        state = client.get(f"/api/diagnostic-sessions/rooms/{room_code}/state", params={"participantId": participant_id})
        assert state.status_code == 200
        active_question = state.json()["activeQuestion"]
        assert active_question["id"] == "Q-DEMO-ATTENTION-01"
        assert "correct" not in str(active_question)
        assert "misconceptionId" not in str(active_question)

        answer = client.post(f"/api/diagnostic-sessions/{session_id}/responses", json={
            "participantId": participant_id,
            "questionId": "Q-DEMO-ATTENTION-01",
            "sectionId": "attention-context-q01",
            "optionId": "B",
            "explanation": "I chose a longer context.",
        })
        assert answer.status_code == 201
        assert answer.json()["response"]["classification"]["label"] == "misunderstood"
        assert answer.json()["response"]["classification"]["misconceptions"] == ["m-attention-02"]
        assert client.get(f"/api/diagnostic-sessions/{session_id}/summary").status_code == 200


def test_demo_endpoints_require_teacher_and_reject_unknown_section() -> None:
    with TestClient(app) as client:
        assert client.get("/api/teaching-agent/demo").status_code == 401
        assert client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "unknown"}).status_code == 401
    with TestClient(app) as client:
        _register_teacher(client)
        response = client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "unknown"})
        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "DEMO_SECTION_NOT_FOUND"


def _batch_payload(count: int, source: dict, *, duplicate: bool = False, invalid_source: bool = False) -> dict:
    questions = []
    for index in range(1, count + 1):
        questions.append({
            "id": f"provider-{index}",
            "topic": "AI & LLM Foundation",
            "concept": "context management",
            "question": "Which context strategy is most appropriate?" if duplicate else f"Which context strategy is most appropriate in case {index}?",
            "learningObjective": "Explain why relevant context matters.",
            "source": [{"type": source["type"], "id": "invented-source" if invalid_source else source["id"]}],
            "options": [
                {"id": "A", "text": "Keep the context relevant and concise.", "correct": True, "misconceptionId": None},
                {"id": "B", "text": "Always include all available context.", "correct": False, "misconceptionId": "m-attention-02"},
                {"id": "C", "text": "Ignore the task instruction.", "correct": False, "misconceptionId": "m-attention-02"},
                {"id": "D", "text": "Treat context as permanent memory.", "correct": False, "misconceptionId": "m-attention-02"},
            ],
        })
    return {"interpretedRequest": {"questionCount": count, "difficulty": "medium", "style": "scenario", "focus": "misconceptions"}, "questions": questions}


class _BatchProvider:
    def __init__(self, payload: dict | Exception) -> None:
        self.payload = payload
        self.calls = 0

    def generate_structured(self, **kwargs) -> ProviderResult:
        self.calls += 1
        if isinstance(self.payload, Exception):
            raise self.payload
        return ProviderResult(data=self.payload, provider="test", model="test-model", latency_ms=1)


def _generate_with_provider(monkeypatch, prompt: str, provider: _BatchProvider):
    analysis = get_preanalyzed_section("attention-context")
    monkeypatch.setenv("AI_MODE", "llm")
    monkeypatch.setattr("app.ai.services.llm_checkpoint_batch_service.create_provider", lambda settings: provider)
    with TestClient(app) as client:
        _register_teacher(client)
        return client.post("/api/teaching-agent/demo/generate", json={"sectionId": "attention-context", "teacherRequest": prompt, "expectedStudents": 30})


def test_agent_generation_uses_one_batch_provider_call(monkeypatch) -> None:
    analysis = get_preanalyzed_section("attention-context")
    provider = _BatchProvider(_batch_payload(5, analysis["allowedSourceRefs"][0]))
    response = _generate_with_provider(monkeypatch, "Tạo 5 câu mức trung bình, tập trung vào misconception.", provider)
    assert response.status_code == 201
    payload = response.json()
    assert provider.calls == 1
    assert len(payload["checkpoints"]) == 5
    assert payload["generation"]["interpretedRequest"]["questionCount"] == 5
    assert payload["generation"]["fallbackUsed"] is False
    assert payload["checkpoints"][0]["sectionId"] == "attention-context-q01"
    assert "correct" not in str(payload["checkpoints"])


def test_generated_checkpoint_still_works_in_the_classroom_workflow(monkeypatch) -> None:
    analysis = get_preanalyzed_section("attention-context")
    provider = _BatchProvider(_batch_payload(1, analysis["allowedSourceRefs"][0]))
    monkeypatch.setenv("AI_MODE", "llm")
    monkeypatch.setattr("app.ai.services.llm_checkpoint_batch_service.create_provider", lambda settings: provider)
    with TestClient(app) as client:
        _register_teacher(client)
        created = client.post("/api/teaching-agent/demo/generate", json={"sectionId": "attention-context", "teacherRequest": "Tạo một câu.", "expectedStudents": 1})
        assert created.status_code == 201
        payload = created.json()
        question = payload["checkpoints"][0]
        assert question["originalSectionId"] == "attention-context"
        assert client.post(f"/api/diagnostic-sessions/{payload['sessionId']}/start").status_code == 200
        joined = client.post("/api/diagnostic-sessions/rooms/join", json={"roomCode": payload["roomCode"], "displayName": "Student"})
        participant_id = joined.json()["participantId"]
        assert client.post(f"/api/diagnostic-sessions/{payload['sessionId']}/checkpoint/{question['id']}/open").status_code == 200
        answered = client.post(f"/api/diagnostic-sessions/{payload['sessionId']}/responses", json={
            "participantId": participant_id,
            "questionId": question["id"],
            "sectionId": question["sectionId"],
            "optionId": "A",
        })
        assert answered.status_code == 201
        assert client.get(f"/api/diagnostic-sessions/{payload['sessionId']}/summary").status_code == 200


def test_agent_generation_accepts_llm_interpreted_single_and_default_counts(monkeypatch) -> None:
    analysis = get_preanalyzed_section("attention-context")
    one_provider = _BatchProvider(_batch_payload(1, analysis["allowedSourceRefs"][0]))
    one_response = _generate_with_provider(monkeypatch, "Cho tôi một câu kiểm tra nhanh.", one_provider)
    assert one_response.status_code == 201
    assert len(one_response.json()["checkpoints"]) == 1

    default_provider = _BatchProvider(_batch_payload(3, analysis["allowedSourceRefs"][0]))
    default_response = _generate_with_provider(monkeypatch, "Tạo vài câu hỏi cho phần này.", default_provider)
    assert default_response.status_code == 201
    assert len(default_response.json()["checkpoints"]) == 3


def test_agent_generation_enforces_llm_count_bound(monkeypatch) -> None:
    analysis = get_preanalyzed_section("attention-context")
    provider = _BatchProvider(_batch_payload(10, analysis["allowedSourceRefs"][0]))
    response = _generate_with_provider(monkeypatch, "Tạo 30 câu.", provider)
    assert response.status_code == 201
    assert len(response.json()["checkpoints"]) == 10
    assert response.json()["generation"]["interpretedRequest"]["questionCount"] == 10


def test_agent_generation_returns_real_provider_failure_without_fallback(monkeypatch) -> None:
    response = _generate_with_provider(monkeypatch, "Tạo một câu.", _BatchProvider(LLMProviderError("safe failure")))
    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_PROVIDER_ERROR"


def test_agent_generation_rejects_invalid_sources_and_duplicate_questions(monkeypatch) -> None:
    analysis = get_preanalyzed_section("attention-context")
    invalid_source = _generate_with_provider(monkeypatch, "Tạo một câu.", _BatchProvider(_batch_payload(1, analysis["allowedSourceRefs"][0], invalid_source=True)))
    assert invalid_source.status_code == 502
    assert invalid_source.json()["detail"]["error"]["code"] == "AI_OUTPUT_INVALID"

    duplicate = _generate_with_provider(monkeypatch, "Tạo hai câu.", _BatchProvider(_batch_payload(2, analysis["allowedSourceRefs"][0], duplicate=True)))
    assert duplicate.status_code == 502
    assert duplicate.json()["detail"]["error"]["code"] == "AI_OUTPUT_INVALID"


def test_agent_generation_rejects_deterministic_mode(monkeypatch) -> None:
    monkeypatch.setenv("AI_MODE", "deterministic")
    with TestClient(app) as client:
        _register_teacher(client)
        response = client.post("/api/teaching-agent/demo/generate", json={"sectionId": "attention-context", "teacherRequest": "Tạo một câu."})
    assert response.status_code == 503
    assert response.json()["detail"]["error"]["code"] == "AI_PROVIDER_CONFIGURATION_ERROR"
