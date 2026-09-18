"""Tests for the fixed, evidence-isolated Teaching Agent demo flow."""

import os
from pathlib import Path
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:3000"
os.environ["AI_MODE"] = "deterministic"

from fastapi.testclient import TestClient  # noqa: E402

from app.ai.data.demo_lesson_catalog import get_demo_lesson, validate_demo_lesson  # noqa: E402
from app.ai.config import AISettings  # noqa: E402
from app.ai.llm.models import LLMDiagnosticResult  # noqa: E402
from app.ai.services import section_checkpoint_service  # noqa: E402
from app.ai.services.section_checkpoint_service import _teaching_context  # noqa: E402
from app.ai.services.section_evidence import build_section_evidence  # noqa: E402
from app.ai.services.slide_evidence import SlideEvidenceError, load_slide_evidence  # noqa: E402
from app.ai.services.transcript_ingestion import TranscriptIngestionError, parse_transcript, select_transcript_segments  # noqa: E402
from app.main import app  # noqa: E402


def _register_teacher(client: TestClient) -> None:
    """Register a fresh teacher in the active TestClient lifespan."""
    response = client.post("/auth/register", json={
        "name": "Demo Teacher",
        "email": f"demo-teacher-{uuid4().hex}@example.com",
        "password": "secure-demo-password",
    })
    assert response.status_code == 201


def test_manifest_validates_d1_and_transcript_04() -> None:
    lesson = validate_demo_lesson()
    assert lesson.id == "day1-ai-llm-foundation"
    assert lesson.slide_path.endswith("d1-slide-hackathon.pdf")
    assert lesson.transcript_path.endswith("transcript-04-clean.md")
    assert len({section.id for section in lesson.sections}) == len(lesson.sections)
    assert all(section.title and section.slide_pages and section.transcript_from and section.transcript_to for section in lesson.sections)


def test_transcript_parser_preserves_order_and_range() -> None:
    segments = parse_transcript("**[T04-001]** First\n\n**[T04-002]** Second\n\n**[T04-003]** Third")
    assert [segment.ref for segment in segments] == ["T04-001", "T04-002", "T04-003"]
    assert [segment.ref for segment in select_transcript_segments(segments, from_ref="T04-002", to_ref="T04-003")] == ["T04-002", "T04-003"]
    try:
        select_transcript_segments(segments, from_ref="T04-003", to_ref="T04-002")
    except TranscriptIngestionError:
        pass
    else:
        raise AssertionError("Unordered transcript ranges must fail.")


def test_slide_loader_rejects_unselected_invalid_page() -> None:
    lesson = get_demo_lesson()
    path = Path(__file__).resolve().parents[3] / lesson.slide_path
    one_page = load_slide_evidence(path, lesson_id=lesson.id, page_numbers=[15])
    assert [item["page"] for item in one_page] == [15]
    assert one_page[0]["ref"] == "slide:day1-ai-llm-foundation:15"
    try:
        load_slide_evidence(path, lesson_id=lesson.id, page_numbers=[30])
    except SlideEvidenceError:
        pass
    else:
        raise AssertionError("Invalid PDF pages must fail.")


def test_evidence_isolation_excludes_neighboring_section_content() -> None:
    selected = build_section_evidence("attention-context")
    neighbor = build_section_evidence("from-llm-to-agent")
    context = _teaching_context(selected)
    assert {item["ref"] for item in selected.slide_evidence} == {
        "slide:day1-ai-llm-foundation:14",
        "slide:day1-ai-llm-foundation:15",
        "slide:day1-ai-llm-foundation:16",
    }
    assert "slide:day1-ai-llm-foundation:23" not in {item["ref"] for item in context["slideEvidence"]}
    assert {item["ref"] for item in neighbor.transcript_evidence}.isdisjoint({item["ref"] for item in context["transcriptEvidence"]})
    assert all(item["text"] not in context["text"] for item in neighbor.transcript_evidence)


def test_demo_selection_and_one_checkpoint_session() -> None:
    with TestClient(app) as client:
        _register_teacher(client)
        selection = client.get("/api/teaching-agent/demo")
        assert selection.status_code == 200
        body = selection.json()
        assert body["agentMessage"] == "Bạn muốn tạo checkpoint cho phần nào?"
        assert body["lesson"]["id"] == "day1-ai-llm-foundation"
        assert "transcript" not in str(body).lower()

        created = client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "attention-context", "expectedStudents": 30})
        assert created.status_code == 201
        result = created.json()
        assert result["status"] == "draft"
        assert result["selectedSection"]["id"] == "attention-context"
        assert len(result["checkpoint"]["sourceRefs"]) == 10
        assert "slide:day1-ai-llm-foundation:15" in result["checkpoint"]["sourceRefs"]
        assert "T04-053" in result["checkpoint"]["sourceRefs"]

        session = client.get(f"/api/diagnostic-sessions/{result['sessionId']}")
        assert session.status_code == 200
        assert len(session.json()["sections"]) == 1
        assert len(session.json()["questions"]) == 1

        question_id = session.json()["questions"][0]["id"]
        assert client.post(f"/api/diagnostic-sessions/{result['sessionId']}/start").status_code == 200
        joined = client.post("/api/diagnostic-sessions/rooms/join", json={"roomCode": result["roomCode"], "displayName": "Anonymous Student"})
        assert joined.status_code == 201
        participant_id = joined.json()["participantId"]
        assert client.post(f"/api/diagnostic-sessions/{result['sessionId']}/checkpoint/{question_id}/open").status_code == 200
        state = client.get(f"/api/diagnostic-sessions/rooms/{result['roomCode']}/state", params={"participantId": participant_id})
        assert state.status_code == 200
        assert state.json()["activeQuestion"]["id"] == question_id
        answer = client.post(f"/api/diagnostic-sessions/{result['sessionId']}/responses", json={
            "participantId": participant_id,
            "questionId": question_id,
            "sectionId": "attention-context",
            "optionId": "A",
        })
        assert answer.status_code == 201
        assert client.get(f"/api/diagnostic-sessions/{result['sessionId']}/summary").status_code == 200


def test_demo_endpoint_requires_teacher_and_rejects_unknown_section() -> None:
    with TestClient(app) as client:
        assert client.get("/api/teaching-agent/demo").status_code == 401
        assert client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "unknown"}).status_code == 401
    with TestClient(app) as client:
        _register_teacher(client)
        response = client.post("/api/teaching-agent/demo/checkpoints", json={"sectionId": "unknown"})
        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "DEMO_SECTION_NOT_FOUND"


def test_section_generation_calls_provider_once_with_only_selected_evidence(monkeypatch) -> None:
    evidence = build_section_evidence("attention-context")
    calls = []

    def fake_generate_llm_diagnostic(*, teaching_context, concept_seed, historical_questions, settings):
        calls.append(teaching_context)
        return LLMDiagnosticResult.model_validate({
            "topic": "Attention & Context",
            "concepts": ["Attention & Context"],
            "learningObjective": "Explain attention using supplied evidence.",
            "misconceptions": [],
            "question": {
                "id": "provider-question",
                "topic": "Attention & Context",
                "concept": "Attention & Context",
                "question": "What does attention do?",
                "learningObjective": "Explain attention using supplied evidence.",
                "source": [{"type": "pdf_page", "id": "slide:day1-ai-llm-foundation:15"}],
                "options": [
                    {"id": "A", "text": "Attention identifies relevant tokens.", "correct": True, "misconceptionId": None},
                    {"id": "B", "text": "Attention ignores all context.", "correct": False, "misconceptionId": None},
                ],
            },
        }), {"mode": "llm", "provider": "test", "model": "test", "latencyMs": 1, "fallbackUsed": False, "fallbackReason": None, "retryCount": 0, "usage": None}

    monkeypatch.setattr(section_checkpoint_service, "generate_llm_diagnostic", fake_generate_llm_diagnostic)
    checkpoint = section_checkpoint_service.generate_checkpoint_for_section(
        evidence,
        settings=AISettings(mode="llm", openai_api_key="test", openai_model="test"),
    )
    assert len(calls) == 1
    assert calls[0]["slideEvidence"] == evidence.slide_evidence
    assert calls[0]["transcriptEvidence"] == evidence.transcript_evidence
    assert "slide:day1-ai-llm-foundation:23" not in str(calls[0])
    assert len(checkpoint.to_dict()["question"]["source"]) == 10
