"""End-to-end tests for the transient anonymous classroom workflow."""

from app.diagnostic.models import DiagnosticSession
from app.diagnostic.repository import InMemoryDiagnosticSessionRepository
from app.diagnostic.service import DiagnosticSessionService


def test_join_open_submit_and_summarize_multiple_choice(monkeypatch) -> None:
    """An anonymous student can answer only the teacher's open checkpoint."""
    monkeypatch.setenv("AI_MODE", "deterministic")
    repository = InMemoryDiagnosticSessionRepository()
    service = DiagnosticSessionService(repository)
    session = DiagnosticSession(
        id="session-1",
        teacher_id="teacher-1",
        room_code="GX-7K2P",
        lesson={"title": "Gradient Descent", "sourceId": "lesson-1"},
        expected_students=1,
        sections=[{
            "section": {"id": "section-1", "title": "Gradient", "order": 1, "sourceRefs": [{"type": "slide", "id": "slide-14"}]},
            "concepts": ["Gradient Descent"],
            "misconceptions": [{"id": "m1", "statement": "It always finds a global minimum."}],
            "question": {
                "id": "Q-123", "concept": "Gradient Descent", "question": "How does gradient descent update parameters?",
                "options": [
                    {"id": "A", "text": "Gradient descent iteratively updates parameters.", "correct": True, "misconceptionId": None},
                    {"id": "B", "text": "It always finds a global minimum.", "correct": False, "misconceptionId": "m1"},
                ],
            },
        }],
    )
    repository.create_session(session)

    service.start_session(session.id)
    joined = service.join_room("GX-7K2P", "Minh")
    assert service.room_state("GX-7K2P", joined["participantId"])["activeQuestion"] is None

    service.open_checkpoint(session.id, "Q-123")
    response = service.submit_response(session.id, joined["participantId"], "Q-123", "section-1", "A")
    assert response.correct is True
    assert response.classification is None

    summary = service.summary(session.id)
    assert summary["respondingStudents"] == 1
    assert summary["sectionResults"][0]["correctRate"] == 1.0
    assert summary["sectionResults"][0]["scoringMethod"] == "answer_key"
    assert summary["sectionResults"][0]["optionDistribution"][0]["count"] == 1


def test_open_all_checkpoints_exposes_every_question_to_a_joined_student() -> None:
    """The classroom can open a generated question set at once without leaking answers."""
    repository = InMemoryDiagnosticSessionRepository()
    service = DiagnosticSessionService(repository)
    session = DiagnosticSession(
        id="session-all", teacher_id="teacher-1", room_code="GX-ALL1", lesson={"title": "Demo", "sourceId": "demo"}, expected_students=1,
        sections=[
            {"section": {"id": "s1", "title": "One", "order": 1, "sourceRefs": []}, "concepts": ["One"], "misconceptions": [], "question": {"id": "Q-1", "concept": "One", "question": "Question one", "options": [{"id": "A", "text": "One", "correct": True, "misconceptionId": None}]}},
            {"section": {"id": "s2", "title": "Two", "order": 2, "sourceRefs": []}, "concepts": ["Two"], "misconceptions": [], "question": {"id": "Q-2", "concept": "Two", "question": "Question two", "options": [{"id": "A", "text": "Two", "correct": True, "misconceptionId": None}]}},
        ],
    )
    repository.create_session(session)
    service.start_session(session.id)
    joined = service.join_room(session.room_code, "Minh")
    service.open_all_checkpoints(session.id)
    state = service.room_state(session.room_code, joined["participantId"])
    assert [item["id"] for item in state["activeQuestions"]] == ["Q-1", "Q-2"]
    assert "correct" not in str(state["activeQuestions"])
    service.submit_response(session.id, joined["participantId"], "Q-1", "s1", "A")
    service.submit_response(session.id, joined["participantId"], "Q-2", "s2", "A")
    assert len(repository.get_session(session.id).responses) == 2
    service.close_all_checkpoints(session.id)
    assert service.room_state(session.room_code, joined["participantId"])["activeQuestions"] == []
