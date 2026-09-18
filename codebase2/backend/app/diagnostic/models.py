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
    student_id: str
    option_id: str
    submitted_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, str]:
        """Serialize an internal response without exposing it through student reads."""
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "questionId": self.question_id,
            "sectionId": self.section_id,
            "studentId": self.student_id,
            "optionId": self.option_id,
            "submittedAt": self.submitted_at,
        }


@dataclass
class DiagnosticSession:
    """A lecturer-created lesson diagnostic and its in-memory answer collection."""

    id: str
    lesson: dict[str, Any]
    sections: list[dict[str, Any]]
    expected_students: int | None
    status: str = "draft"
    responses: list[StudentResponse] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
