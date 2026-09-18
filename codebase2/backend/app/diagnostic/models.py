"""Domain models for the transient diagnostic-session workflow."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    """Return an ISO timestamp suitable for in-memory prototype records."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StudentResponse:
    """A student's latest answer to one question in one diagnostic session."""

    id: str
    session_id: str
    question_id: str
    section_id: str
    participant_id: str
    option_id: str
    explanation: str | None = None
    correct: bool = False
    classification: dict[str, object] | None = None
    submitted_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, str]:
        """Serialize an internal response without exposing it through student reads."""
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "questionId": self.question_id,
            "sectionId": self.section_id,
            "participantId": self.participant_id,
            "optionId": self.option_id,
            "explanation": self.explanation,
            "correct": self.correct,
            "classification": self.classification,
            "submittedAt": self.submitted_at,
        }


@dataclass
class DiagnosticSession:
    """A lecturer-created lesson diagnostic and its in-memory answer collection."""

    id: str
    teacher_id: str | None
    room_code: str
    lesson: dict[str, Any]
    sections: list[dict[str, Any]]
    expected_students: int | None
    status: str = "draft"
    participants: dict[str, str] = field(default_factory=dict)
    active_question_id: str | None = None
    active_question_ids: list[str] = field(default_factory=list)
    # Live sessions start with plans only; generated questions are appended at runtime.
    checkpoint_plans: list[dict[str, Any]] = field(default_factory=list)
    current_slide: int = 1
    current_transcript_ref: str | None = None
    responses: list[StudentResponse] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
