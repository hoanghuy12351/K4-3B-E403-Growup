"""Application service that joins AI generation with session-state workflow."""

from typing import Any
from uuid import uuid4

from app.ai.config import AISettings
from app.ai.services.lesson_diagnostic_service import generate_lesson_diagnostic
from app.ai.services.material_ingestion import ingest_material, resolve_available_material

from .aggregation import build_class_summary
from .models import DiagnosticSession, StudentResponse
from .repository import DiagnosticSessionRepository, SessionNotFoundError


class SessionValidationError(ValueError):
    """Raised when a student response does not match its generated session."""


class DiagnosticSessionService:
    """Coordinate material ingestion, per-section AI calls, and transient storage."""

    def __init__(self, repository: DiagnosticSessionRepository) -> None:
        self.repository = repository

    def create_session(self, lesson: dict[str, Any], expected_students: int | None, settings: AISettings | None = None) -> DiagnosticSession:
        """Generate one diagnostic per section and save the session as lecturer-reviewable draft."""
        if lesson.get("materialId"):
            lesson = resolve_available_material(str(lesson["materialId"]))
        material = ingest_material(lesson)
        section_diagnostics = generate_lesson_diagnostic(material, settings=settings)
        session = DiagnosticSession(
            id=str(uuid4()),
            lesson={"title": material.title, "sourceId": material.source_id, "sourceBlocks": [block.to_dict() for block in material.blocks]},
            sections=[item.to_dict() for item in section_diagnostics],
            expected_students=expected_students,
        )
        return self.repository.create_session(session)

    def get_session(self, session_id: str) -> DiagnosticSession:
        """Read a session through the replaceable persistence boundary."""
        return self.repository.get_session(session_id)

    def start_session(self, session_id: str) -> DiagnosticSession:
        """Mark lecturer-reviewed draft material as available for student responses."""
        session = self.get_session(session_id)
        session.status = "active"
        return session

    def submit_response(self, session_id: str, student_id: str, question_id: str, section_id: str, option_id: str) -> StudentResponse:
        """Validate session ownership then save the student's latest answer to that question."""
        session = self.get_session(session_id)
        if session.status != "active":
            raise SessionValidationError("The lecturer must start this diagnostic session before students respond.")
        question_section = next((item for item in session.sections if item["question"]["id"] == question_id), None)
        if question_section is None:
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        if question_section["section"]["id"] != section_id:
            raise SessionValidationError("The section does not match the selected question.")
        if not any(option.get("id") == option_id for option in question_section["question"].get("options", [])):
            raise SessionValidationError("The selected option does not belong to this question.")
        response = StudentResponse(
            id=str(uuid4()),
            session_id=session.id,
            question_id=question_id,
            section_id=section_id,
            student_id=student_id,
            option_id=option_id,
        )
        return self.repository.save_response(response)

    def summary(self, session_id: str) -> dict[str, Any]:
        """Build a non-identifying lecturer summary from the stored session responses."""
        return build_class_summary(self.get_session(session_id))

    @staticmethod
    def student_view(session: DiagnosticSession) -> dict[str, Any]:
        """Serialize student-safe questions without correctness or raw response data."""
        return {
            "sessionId": session.id,
            "lesson": {"title": session.lesson["title"], "sourceId": session.lesson["sourceId"]},
            "status": session.status,
            "createdAt": session.created_at,
            "sections": [
                {"id": item["section"]["id"], "title": item["section"]["title"], "order": item["section"]["order"], "sourceRefs": item["section"]["sourceRefs"], "concepts": item["concepts"]}
                for item in session.sections
            ],
            "questions": [
                {
                    **{key: value for key, value in item["question"].items() if key != "options"},
                    "sectionId": item["section"]["id"],
                    "options": [{key: value for key, value in option.items() if key != "correct"} for option in item["question"]["options"]],
                }
                for item in session.sections
            ],
        }
