"""End-to-end tests for the transient anonymous classroom workflow."""

from app.diagnostic.models import DiagnosticSession
from app.diagnostic.repository import InMemoryDiagnosticSessionRepository
from app.diagnostic.service import DiagnosticSessionService


def test_join_open_submit_classify_and_summarize(monkeypatch) -> None:
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
    response = service.submit_response(
        session.id, joined["participantId"], "Q-123", "section-1", "A",
        "Gradient descent iteratively updates parameters.",
    )
    assert response.correct is True
    assert response.classification and response.classification["label"] == "understood"

    summary = service.summary(session.id)
    assert summary["respondingStudents"] == 1
    assert summary["sectionResults"][0]["correctRate"] == 1.0
    assert summary["sectionResults"][0]["understandingDistribution"]["understood"] == 1
