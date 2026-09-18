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
    checkpoint_run_id: str
    correct: bool = False
    signal: str = "incorrect_choice"
    misconception_id: str | None = None
    submitted_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize an internal response without exposing it through student reads."""
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "questionId": self.question_id,
            "sectionId": self.section_id,
            "participantId": self.participant_id,
            "optionId": self.option_id,
            "checkpointRunId": self.checkpoint_run_id,
            "correct": self.correct,
            "signal": self.signal,
            "misconceptionId": self.misconception_id,
            "submittedAt": self.submitted_at,
        }


@dataclass
class CheckpointRun:
    """One collection window for a question that may be opened more than once."""

    id: str
    session_id: str
    question_id: str
    status: str = "collecting"
    response_version: int = 0
    analysis_id: str | None = None
    opened_at: str = field(default_factory=utc_now)
    closed_at: str | None = None


@dataclass
class ClassAssessment:
    """Persisted aggregate snapshot and its optional AI teaching report."""

    id: str
    session_id: str
    checkpoint_run_id: str
    question_id: str
    status: str = "analyzing"
    metrics: dict[str, Any] = field(default_factory=dict)
    computed_status: str | None = None
    ai_assessment: dict[str, Any] | None = None
    error_code: str | None = None
    created_at: str = field(default_factory=utc_now)
    completed_at: str | None = None


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
    active_checkpoint_run_id: str | None = None
    responses: list[StudentResponse] = field(default_factory=list)
    checkpoint_runs: dict[str, CheckpointRun] = field(default_factory=dict)
    assessments: dict[str, ClassAssessment] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
