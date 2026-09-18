"""Application service that joins AI generation with session-state workflow."""

from typing import Any
from secrets import choice
from uuid import uuid4

from app.ai.config import AISettings
from app.ai.services.lesson_diagnostic_service import generate_lesson_diagnostic
from app.ai.services.material_ingestion import ingest_material, resolve_available_material
from app.ai.services.answer_classification_service import classify_explanation
from app.domain.classification import rubric_from_diagnostic

from .aggregation import build_class_summary
from .models import DiagnosticSession, StudentResponse
from .repository import DiagnosticSessionRepository, SessionNotFoundError


class SessionValidationError(ValueError):
    """Raised when a student response does not match its generated session."""


class DiagnosticSessionService:
    """Coordinate material ingestion, per-section AI calls, and transient storage."""

    def __init__(self, repository: DiagnosticSessionRepository) -> None:
        self.repository = repository

    def create_session(self, lesson: dict[str, Any], expected_students: int | None, teacher_id: str | None = None, settings: AISettings | None = None) -> DiagnosticSession:
        """Generate one diagnostic per section and save the session as lecturer-reviewable draft."""
        if lesson.get("materialId"):
            lesson = resolve_available_material(str(lesson["materialId"]))
        material = ingest_material(lesson)
        section_diagnostics = generate_lesson_diagnostic(material, settings=settings)
        session = DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson={
                "materialId": lesson.get("materialId"),
                "title": material.title,
                "sourceId": material.source_id,
                "contentMode": "mock_pdf_extract" if all(block.source_type == "mock_pdf" for block in material.blocks) else "text",
                "sourceBlocks": [block.to_dict() for block in material.blocks],
            },
            sections=[item.to_dict() for item in section_diagnostics],
            expected_students=expected_students,
        )
        return self.repository.create_session(session)

    def _room_code(self) -> str:
        """Generate a short public code while keeping the UUID internal."""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(20):
            code = "GX-" + "".join(choice(alphabet) for _ in range(4))
            try:
                self.repository.get_session_by_room_code(code)
            except SessionNotFoundError:
                return code
        raise RuntimeError("Could not generate a unique room code.")

    def get_session(self, session_id: str) -> DiagnosticSession:
        """Read a session through the replaceable persistence boundary."""
        return self.repository.get_session(session_id)

    def start_session(self, session_id: str) -> DiagnosticSession:
        """Mark lecturer-reviewed draft material as available for student responses."""
        session = self.get_session(session_id)
        session.status = "ready"
        return session

    def join_room(self, room_code: str, display_name: str) -> dict[str, str]:
        """Create a transient anonymous participant without creating a user account."""
        session = self.repository.get_session_by_room_code(room_code.strip().upper())
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("The classroom is not available for joining yet.")
        participant_id = f"anon_{uuid4().hex[:12]}"
        session.participants[participant_id] = display_name.strip()
        return {"participantId": participant_id, "sessionId": session.id, "roomCode": session.room_code}

    def room_state(self, room_code: str, participant_id: str) -> dict[str, Any]:
        """Return only the active question and public classroom state to a joined student."""
        session = self.repository.get_session_by_room_code(room_code.strip().upper())
        if participant_id not in session.participants:
            raise SessionValidationError("The participant is not joined to this room.")
        active = next((item for item in session.sections if item["question"]["id"] == session.active_question_id), None)
        question = None
        if active:
            question = {
                **{key: value for key, value in active["question"].items() if key not in {"options", "correct", "rubric"}},
                "sectionId": active["section"]["id"],
                "options": [{key: value for key, value in option.items() if key not in {"correct", "misconceptionId"}} for option in active["question"]["options"]],
            }
        return {"sessionId": session.id, "roomCode": session.room_code, "status": session.status, "activeQuestion": question}

    def open_checkpoint(self, session_id: str, question_id: str) -> DiagnosticSession:
        """Open exactly one generated checkpoint for a live classroom."""
        session = self.get_session(session_id)
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("Start the classroom before opening a checkpoint.")
        if not any(item["question"]["id"] == question_id for item in session.sections):
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        session.status = "live"
        session.active_question_id = question_id
        return session

    def close_checkpoint(self, session_id: str, question_id: str) -> DiagnosticSession:
        """Hide the active checkpoint while leaving the classroom live."""
        session = self.get_session(session_id)
        if session.active_question_id != question_id:
            raise SessionValidationError("The requested checkpoint is not open.")
        session.active_question_id = None
        return session

    def submit_response(self, session_id: str, participant_id: str, question_id: str, section_id: str, option_id: str, explanation: str | None = None) -> StudentResponse:
        """Validate session ownership then save the student's latest answer to that question."""
        session = self.get_session(session_id)
        if session.status != "live" or session.active_question_id != question_id:
            raise SessionValidationError("This checkpoint is not open for responses.")
        if participant_id not in session.participants:
            raise SessionValidationError("The participant is not joined to this classroom.")
        question_section = next((item for item in session.sections if item["question"]["id"] == question_id), None)
        if question_section is None:
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        if question_section["section"]["id"] != section_id:
            raise SessionValidationError("The section does not match the selected question.")
        if not any(option.get("id") == option_id for option in question_section["question"].get("options", [])):
            raise SessionValidationError("The selected option does not belong to this question.")
        selected_option = next(option for option in question_section["question"]["options"] if option.get("id") == option_id)
        classification = None
        if explanation:
            rubric = rubric_from_diagnostic(question_section)
            classification = classify_explanation(rubric=rubric, explanation=explanation, settings=AISettings.from_env()).to_dict()
        response = StudentResponse(
            id=str(uuid4()),
            session_id=session.id,
            question_id=question_id,
            section_id=section_id,
            participant_id=participant_id,
            option_id=option_id,
            explanation=explanation,
            correct=bool(selected_option.get("correct")),
            classification=classification,
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
            "roomCode": session.room_code,
            "lesson": {"title": session.lesson["title"], "sourceId": session.lesson["sourceId"]},
            "status": session.status,
            "activeQuestionId": session.active_question_id,
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
