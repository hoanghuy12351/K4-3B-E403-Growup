"""Focused tests for runtime live transcript checkpoint generation."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.ai.config import AISettings
from app.ai.llm.errors import LLMProviderError
from app.ai.llm.models import ProviderResult
from app.ai.services.live_transcript_simulator import visible_segments
from app.ai.services.transcript_ingestion import TranscriptSegment
from app.diagnostic.repository import InMemoryDiagnosticSessionRepository
from app.diagnostic.service import DiagnosticSessionService, SessionValidationError
from app.main import app


class FakeProvider:
    """Record the real-generation contract without reaching an external provider."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls = 0
        self.user_prompt = ""

    def generate_structured(self, **kwargs) -> ProviderResult:
        self.calls += 1
        self.user_prompt = kwargs["user_prompt"]
        if self.failure:
            raise self.failure
        return ProviderResult(
            data={
                "interpretedRequest": {"questionCount": 1, "difficulty": "medium", "style": "conceptual", "focus": "live lecture"},
                "questions": [{
                    "id": "provider-question", "topic": "AI & LLM Foundation", "concept": "attention",
                    "question": "Vì sao attention quan trọng với Transformer?",
                    "learningObjective": "Giải thích vai trò của attention.",
                    "source": [{"type": "pdf_page", "id": "slide:day1-ai-llm-foundation:5"}],
                    "options": [
                        {"id": "A", "text": "Nó giúp mô hình tập trung vào phần liên quan.", "correct": True, "misconceptionId": None},
                        {"id": "B", "text": "Nó thay toàn bộ dữ liệu huấn luyện.", "correct": False, "misconceptionId": None},
                        {"id": "C", "text": "Nó tạo đáp án hoàn chỉnh một lần.", "correct": False, "misconceptionId": None},
                        {"id": "D", "text": "Nó bỏ qua ngữ cảnh đầu vào.", "correct": False, "misconceptionId": None},
                    ],
                }],
            },
            provider="fake", model="fake-model", latency_ms=1,
        )


def _service() -> DiagnosticSessionService:
    return DiagnosticSessionService(InMemoryDiagnosticSessionRepository())


def _live_session(service: DiagnosticSessionService, selections: list[dict] | None = None):
    return service.create_live_session(
        teacher_id="teacher-1", lesson_id="day1-ai-llm-foundation", expected_students=3,
        selections=selections or [{"sectionId": "transformer-breakthrough", "teacherPrompt": "Focus on attention.", "triggerSlide": 9}],
    )


def _reach_transformer(service: DiagnosticSessionService, session_id: str) -> None:
    service.update_live_state(session_id, current_slide=9, current_transcript_ref="T04-041")


def test_multiple_plans_are_ordered_and_duplicate_selection_is_rejected() -> None:
    service = _service()
    session = _live_session(service, [
        {"sectionId": "llm-to-agent", "teacherPrompt": "Compare LLM and agents."},
        {"sectionId": "transformer-breakthrough", "teacherPrompt": "Ask about attention."},
        {"sectionId": "llm-mechanics", "teacherPrompt": "Ask about next-token prediction."},
    ])
    assert [item["sectionId"] for item in session.checkpoint_plans] == ["transformer-breakthrough", "llm-mechanics", "llm-to-agent"]
    assert session.sections == []
    assert all(item["status"] == "planned" for item in session.checkpoint_plans)
    with pytest.raises(SessionValidationError, match="only be selected once"):
        _live_session(service, [
            {"sectionId": "transformer-breakthrough", "teacherPrompt": "One."},
            {"sectionId": "transformer-breakthrough", "teacherPrompt": "Two."},
        ])


def test_visible_segments_never_include_future_refs() -> None:
    segments = [TranscriptSegment(ref=f"T04-00{index}", text=f"segment {index}") for index in range(1, 5)]
    assert [item.ref for item in visible_segments(segments, "T04-002")] == ["T04-001", "T04-002"]


def test_runtime_generation_uses_bounded_transcript_and_slide_evidence() -> None:
    service = _service()
    session = _live_session(service)
    _reach_transformer(service, session.id)
    provider = FakeProvider()
    _, plan, generated = service.trigger_live_checkpoint(session.id, "cp-transformer-breakthrough", settings=AISettings(mode="llm"), provider=provider)
    assert generated is True
    assert provider.calls == 1
    assert "Focus on attention." in provider.user_prompt
    assert "T04-041" in provider.user_prompt
    assert "T04-042" not in provider.user_prompt
    assert "slide:day1-ai-llm-foundation:9" in provider.user_prompt
    assert "slide:day1-ai-llm-foundation:10" not in provider.user_prompt
    assert plan["status"] == "open"


def test_duplicate_trigger_does_not_repeat_provider_or_question_records() -> None:
    service = _service()
    session = _live_session(service)
    _reach_transformer(service, session.id)
    provider = FakeProvider()
    service.trigger_live_checkpoint(session.id, "cp-transformer-breakthrough", settings=AISettings(mode="llm"), provider=provider)
    _, _, generated = service.trigger_live_checkpoint(session.id, "cp-transformer-breakthrough", settings=AISettings(mode="llm"), provider=provider)
    assert generated is False
    assert provider.calls == 1
    assert len(session.sections) == 1


def test_provider_failure_keeps_checkpoint_retryable_without_active_question() -> None:
    service = _service()
    session = _live_session(service)
    _reach_transformer(service, session.id)
    with pytest.raises(LLMProviderError):
        service.trigger_live_checkpoint(session.id, "cp-transformer-breakthrough", settings=AISettings(mode="llm"), provider=FakeProvider(LLMProviderError("safe failure")))
    assert session.checkpoint_plans[0]["status"] == "failed"
    assert session.sections == []
    assert session.active_question_ids == []


def test_generated_question_keeps_student_room_state_private_and_aggregates_answers() -> None:
    service = _service()
    session = _live_session(service)
    service.start_session(session.id)
    _reach_transformer(service, session.id)
    service.trigger_live_checkpoint(session.id, "cp-transformer-breakthrough", settings=AISettings(mode="llm"), provider=FakeProvider())
    joined = service.join_room(session.room_code, "Student")
    state = service.room_state(session.room_code, joined["participantId"])
    assert state["activeQuestion"]
    assert "correct" not in str(state["activeQuestion"])
    question = session.sections[0]["question"]
    service.submit_response(session.id, joined["participantId"], question["id"], session.sections[0]["section"]["id"], "A")
    result = service.summary(session.id)["sectionResults"][0]
    assert result["correctRate"] == 1


def test_live_slide_deck_endpoint_is_teacher_only_and_streams_the_canonical_pdf() -> None:
    """Ensure the presentation screen uses the existing canonical PDF, not a mock asset."""
    with TestClient(app) as client:
        assert client.get("/api/teaching-agent/live-lesson/slides").status_code == 401
        registered = client.post("/auth/register", json={
            "name": "Slide Teacher",
            "email": f"slide-teacher-{uuid4().hex}@example.com",
            "password": "secure-demo-password",
        })
        assert registered.status_code == 201
        response = client.get("/api/teaching-agent/live-lesson/slides")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.content.startswith(b"%PDF")
