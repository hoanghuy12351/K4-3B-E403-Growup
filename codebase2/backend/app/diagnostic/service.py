"""Application service that joins AI generation with session-state workflow."""

from typing import Any
from secrets import choice
from uuid import uuid4

from app.ai.config import AISettings
from app.ai.services.class_assessment_service import generate_class_assessment
from app.ai.services.lesson_diagnostic_service import generate_lesson_diagnostic
from app.ai.services.material_ingestion import ingest_material, resolve_available_material
from app.ai.services.selection_service import classify_selection
from app.domain.classification import rubric_from_diagnostic

from .aggregation import build_checkpoint_metrics, build_class_summary
from .models import ClassAssessment, CheckpointRun, DiagnosticSession, StudentResponse, utc_now
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

    def require_teacher(self, session_id: str, teacher_id: str) -> DiagnosticSession:
        """Ensure one authenticated teacher cannot control another teacher's session."""
        session = self.get_session(session_id)
        if session.teacher_id and session.teacher_id != teacher_id:
            raise SessionValidationError("This classroom belongs to another teacher.")
        return session

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
        return {
            "sessionId": session.id,
            "roomCode": session.room_code,
            "status": session.status,
            "checkpointRunId": session.active_checkpoint_run_id,
            "activeQuestion": question,
        }

    def open_checkpoint(self, session_id: str, question_id: str) -> tuple[DiagnosticSession, CheckpointRun]:
        """Open a new response-collection run for exactly one question."""
        session = self.get_session(session_id)
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("Start the classroom before opening a checkpoint.")
        if session.active_checkpoint_run_id:
            raise SessionValidationError("Close the active checkpoint before opening another one.")
        if not any(item["question"]["id"] == question_id for item in session.sections):
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        run = CheckpointRun(
            id=str(uuid4()), session_id=session.id, question_id=question_id
        )
        session.checkpoint_runs[run.id] = run
        session.status = "live"
        session.active_question_id = question_id
        session.active_checkpoint_run_id = run.id
        return session, run

    def close_checkpoint(self, session_id: str, question_id: str) -> ClassAssessment:
        """Lock the active run and create an immutable analysis job."""
        session = self.get_session(session_id)
        if session.active_question_id != question_id:
            raise SessionValidationError("The requested checkpoint is not open.")
        run = session.checkpoint_runs.get(session.active_checkpoint_run_id or "")
        if run is None:
            raise SessionValidationError("The active checkpoint run is unavailable.")
        run.status = "analyzing"
        run.closed_at = utc_now()
        assessment = ClassAssessment(
            id=str(uuid4()),
            session_id=session.id,
            checkpoint_run_id=run.id,
            question_id=question_id,
        )
        run.analysis_id = assessment.id
        session.assessments[assessment.id] = assessment
        session.active_question_id = None
        session.active_checkpoint_run_id = None
        return assessment

    def analyze_checkpoint(
        self,
        session_id: str,
        checkpoint_run_id: str,
        settings: AISettings | None = None,
    ) -> ClassAssessment:
        """Aggregate a closed run and generate one teacher-facing AI report."""

        session = self.get_session(session_id)
        run = session.checkpoint_runs.get(checkpoint_run_id)
        if run is None or not run.analysis_id:
            raise SessionNotFoundError("Checkpoint analysis was not found.")
        assessment = session.assessments[run.analysis_id]
        try:
            metrics, computed_status = build_checkpoint_metrics(session, run)
            assessment.metrics = metrics
            assessment.computed_status = computed_status
            assessment.ai_assessment = generate_class_assessment(
                metrics=metrics,
                computed_status=computed_status,
                settings=settings or AISettings.from_env(),
            )
            assessment.status = "completed"
            assessment.completed_at = utc_now()
            run.status = "analyzed"
        except Exception:
            # Background jobs must leave an inspectable state without persisting
            # provider secrets or raw exception messages in the public result.
            assessment.status = "failed"
            assessment.error_code = "ASSESSMENT_GENERATION_FAILED"
            assessment.completed_at = utc_now()
            run.status = "failed"
        return assessment

    def get_checkpoint_analysis(
        self, session_id: str, checkpoint_run_id: str
    ) -> ClassAssessment:
        """Return the analysis owned by a particular session and run."""

        session = self.get_session(session_id)
        run = session.checkpoint_runs.get(checkpoint_run_id)
        if run is None or not run.analysis_id:
            raise SessionNotFoundError("Checkpoint analysis was not found.")
        return session.assessments[run.analysis_id]

    def submit_response(self, session_id: str, participant_id: str, question_id: str, section_id: str, option_id: str) -> StudentResponse:
        """Validate session ownership then save the student's latest answer to that question."""
        session = self.get_session(session_id)
        if session.status != "live" or session.active_question_id != question_id:
            raise SessionValidationError("This checkpoint is not open for responses.")
        if not session.active_checkpoint_run_id:
            raise SessionValidationError("This checkpoint has no active collection run.")
        if participant_id not in session.participants:
            raise SessionValidationError("The participant is not joined to this classroom.")
        question_section = next((item for item in session.sections if item["question"]["id"] == question_id), None)
        if question_section is None:
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        if question_section["section"]["id"] != section_id:
            raise SessionValidationError("The section does not match the selected question.")
        if not any(option.get("id") == option_id for option in question_section["question"].get("options", [])):
            raise SessionValidationError("The selected option does not belong to this question.")
        rubric = rubric_from_diagnostic(question_section)
        selection = classify_selection(rubric=rubric, selected_option_id=option_id)
        response = StudentResponse(
            id=str(uuid4()),
            session_id=session.id,
            question_id=question_id,
            section_id=section_id,
            participant_id=participant_id,
            option_id=option_id,
            checkpoint_run_id=session.active_checkpoint_run_id,
            correct=selection.correct,
            signal=selection.signal,
            misconception_id=selection.misconception_id,
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
                    "options": [
                        {key: value for key, value in option.items() if key not in {"correct", "misconceptionId"}}
                        for option in item["question"]["options"]
                    ],
                }
                for item in session.sections
            ],
        }
