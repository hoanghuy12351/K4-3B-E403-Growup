"""FastAPI routes for lecturer and student diagnostic-session workflows."""

import logging
from typing import Annotated
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai import AISettings
from app.ai.llm.errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, LLMValidationError
from app.ai.services.material_ingestion import MaterialIngestionError, list_available_materials
from app.diagnostic.repository import InMemoryDiagnosticSessionRepository, SessionNotFoundError
from app.diagnostic.service import DiagnosticSessionService, SessionValidationError
from app.models.user import Teacher
from app.models.material import LessonMaterial
from app.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.routers.auth import current_teacher
from app.schemas.diagnostic_session import CreateDiagnosticSessionRequest, JoinRoomRequest, LiveCheckpointRegenerateRequest, LiveStateRequest, StudentResponseRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagnostic-sessions", tags=["Diagnostic sessions"])
repository = InMemoryDiagnosticSessionRepository()
service = DiagnosticSessionService(repository)


def _not_found() -> HTTPException:
    """Return a stable missing-session response without disclosing internal state."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "The diagnostic session was not found."}})


def _provider_unavailable() -> HTTPException:
    """Return a safe provider-configuration response."""
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "AI_PROVIDER_CONFIGURATION_ERROR", "message": "The configured AI provider requires a valid API key and model configuration."}})


def _provider_authentication_rejected() -> HTTPException:
    """Return a safe credential-rejection response without revealing secret values."""
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "AI_PROVIDER_AUTHENTICATION_ERROR", "message": "The configured AI provider rejected the server credentials."}})


@router.get("/lesson-materials")
def get_lesson_materials(teacher: Annotated[Teacher, Depends(current_teacher)], db: Annotated[Session, Depends(get_db)]) -> dict[str, list[dict[str, str]]]:
    """Return selectable PDF lessons discovered from the repository data directory."""
    try:
        uploaded = db.scalars(select(LessonMaterial).where(LessonMaterial.teacher_id == teacher.id)).all()
        return {"materials": [{"id": item.id, "title": item.title, "sourceId": item.id, "type": item.media_type} for item in uploaded]}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "MATERIAL_DATA_UNAVAILABLE", "message": "Local lesson material is unavailable."}}) from None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(request: CreateDiagnosticSessionRequest, teacher: Annotated[Teacher, Depends(current_teacher)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Create a lecturer-reviewable draft with one generated question per section."""
    try:
        lesson = request.lesson.model_dump(by_alias=True, exclude_none=True)
        material_id = lesson.get("materialId")
        if material_id:
            material = db.scalar(select(LessonMaterial).where(LessonMaterial.id == material_id, LessonMaterial.teacher_id == teacher.id))
            if not material:
                raise MaterialIngestionError("The selected lesson material is unavailable.")
            lesson = {"materialId": material.id, "title": material.title, "sourceId": material.id, "sourceBlocks": material.source_blocks}
        session = service.create_session(
            lesson=lesson,
            expected_students=request.expected_students,
            teacher_id=teacher.id,
            settings=AISettings.from_env(),
        )
        return {
            "sessionId": session.id,
            "roomCode": session.room_code,
            "lesson": session.lesson,
            "sections": session.sections,
            "status": session.status,
            "createdAt": session.created_at,
        }
    except MaterialIngestionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_MATERIAL", "message": str(error)}}) from None
    except FileNotFoundError:
        logger.warning("Diagnostic session evidence data is unavailable.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "AI_DATA_UNAVAILABLE", "message": "The diagnostic dataset is currently unavailable."}}) from None
    except LLMConfigurationError:
        logger.warning("Diagnostic session provider configuration is unavailable.")
        raise _provider_unavailable() from None
    except LLMAuthenticationError:
        logger.warning("Diagnostic session provider authentication was rejected.")
        raise _provider_authentication_rejected() from None
    except LLMTimeoutError:
        logger.warning("Diagnostic session provider timed out.")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"error": {"code": "AI_PROVIDER_TIMEOUT", "message": "The AI provider timed out while generating diagnostic questions."}}) from None
    except (LLMProviderError, LLMRateLimitError, LLMMalformedResponseError, LLMValidationError) as error:
        logger.warning("Diagnostic generation failed: %s: %s", type(error).__name__, str(error))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_PROVIDER_ERROR", "message": "The configured AI provider could not generate diagnostic questions."}}) from None
    except (TypeError, ValueError):
        logger.warning("Diagnostic session configuration or generation result is invalid.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "AI_CONFIGURATION_ERROR", "message": "The AI diagnostic service is not configured correctly."}}) from None


@router.post("/{session_id}/start")
def start_session(session_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, str]:
    """Allow the lecturer to mark a reviewed draft as active for students."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.start_session(session_id)
        return {"sessionId": session.id, "roomCode": session.room_code, "status": session.status}
    except SessionNotFoundError:
        raise _not_found() from None


@router.get("/{session_id}")
def get_teacher_session(session_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Return checkpoint review data only to the owning teacher."""
    try:
        return service.teacher_view(service.require_teacher(session_id, teacher.id))
    except SessionNotFoundError:
        raise _not_found() from None


@router.post("/{session_id}/live-state")
def update_live_state(session_id: str, request: LiveStateRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Persist the teacher's bounded, monotonic live slide/transcript cursor."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.update_live_state(session_id, **request.model_dump())
        return {"sessionId": session.id, "currentSlide": session.current_slide, "currentTranscriptRef": session.current_transcript_ref}
    except SessionNotFoundError:
        raise _not_found() from None
    except (SessionValidationError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_LIVE_STATE", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoints/{plan_id}/trigger")
def trigger_live_checkpoint(session_id: str, plan_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Run the configured real LLM only when the selected live boundary is reached."""
    settings: AISettings | None = None
    try:
        service.require_teacher(session_id, teacher.id)
        settings = AISettings.from_env()
        session, plan, generated = service.trigger_live_checkpoint(session_id, plan_id, settings=settings)
        return {"sessionId": session.id, "checkpointPlan": plan, "generated": generated, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_LIVE_CHECKPOINT", "message": str(error)}}) from None
    except LLMConfigurationError as error:
        logger.warning("Live checkpoint configuration failed: provider=%s model=%s error=%s", settings.provider if settings else "unknown", getattr(settings, f"{settings.provider}_model", "unknown") if settings else "unknown", type(error).__name__)
        raise _provider_unavailable() from None
    except LLMAuthenticationError:
        raise _provider_authentication_rejected() from None
    except LLMTimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"error": {"code": "AI_PROVIDER_TIMEOUT", "message": "The AI provider took too long to create this checkpoint."}}) from None
    except (LLMMalformedResponseError, LLMValidationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_OUTPUT_INVALID", "message": "The AI returned an invalid checkpoint format. Please retry."}}) from None
    except (LLMProviderError, LLMRateLimitError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_PROVIDER_ERROR", "message": "The configured AI provider could not create this checkpoint."}}) from None


@router.post("/{session_id}/checkpoints/{plan_id}/close")
def close_live_checkpoint(session_id: str, plan_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Close a runtime-generated plan and let the lecturer continue the lesson."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.close_live_checkpoint(session_id, plan_id)
        return {"sessionId": session.id, "status": session.status, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_LIVE_CHECKPOINT", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoints/{plan_id}/open")
def open_live_checkpoint(session_id: str, plan_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Expose a lecturer-reviewed runtime checkpoint to the joined students."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.open_live_checkpoint(session_id, plan_id)
        return {"sessionId": session.id, "status": session.status, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_LIVE_CHECKPOINT", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoints/{plan_id}/regenerate")
def regenerate_live_checkpoint(session_id: str, plan_id: str, request: LiveCheckpointRegenerateRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Use lecturer feedback to replace a private preview with a real LLM result."""
    settings: AISettings | None = None
    try:
        service.require_teacher(session_id, teacher.id)
        settings = AISettings.from_env()
        session, plan, generated = service.regenerate_live_checkpoint(session_id, plan_id, teacher_prompt=request.teacher_prompt, settings=settings)
        return {"sessionId": session.id, "checkpointPlan": plan, "generated": generated, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_LIVE_CHECKPOINT", "message": str(error)}}) from None
    except LLMConfigurationError:
        raise _provider_unavailable() from None
    except LLMAuthenticationError:
        raise _provider_authentication_rejected() from None
    except LLMTimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"error": {"code": "AI_PROVIDER_TIMEOUT", "message": "The AI provider took too long to create this checkpoint."}}) from None
    except (LLMMalformedResponseError, LLMValidationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_OUTPUT_INVALID", "message": "The AI returned an invalid checkpoint format. Please retry."}}) from None
    except (LLMProviderError, LLMRateLimitError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_PROVIDER_ERROR", "message": "The configured AI provider could not create this checkpoint."}}) from None


@router.post("/{session_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_student_response(session_id: str, request: StudentResponseRequest) -> dict[str, Any]:
    """Store a student's latest option selection for one validated session question."""
    try:
        response = service.submit_response(session_id=session_id, **request.model_dump())
        return {"response": response.to_dict(), "answerPolicy": "latest_answer_replaces_previous"}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoint/{question_id}/open")
def open_checkpoint(session_id: str, question_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, str | None]:
    """Make a single checkpoint visible to joined students."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.open_checkpoint(session_id, question_id)
        return {"sessionId": session.id, "status": session.status, "activeQuestionId": session.active_question_id}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoint/{question_id}/close")
def close_checkpoint(session_id: str, question_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, str | None]:
    """Hide an active checkpoint without ending the classroom."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.close_checkpoint(session_id, question_id, settings=AISettings.from_env())
        return {"sessionId": session.id, "status": session.status, "activeQuestionId": session.active_question_id}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None
    except LLMConfigurationError:
        raise _provider_unavailable() from None
    except LLMAuthenticationError:
        raise _provider_authentication_rejected() from None
    except LLMTimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"error": {"code": "AI_PROVIDER_TIMEOUT", "message": "AI mất quá lâu để phân tích kết quả lớp."}}) from None
    except (LLMProviderError, LLMRateLimitError, LLMMalformedResponseError, LLMValidationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_ANALYSIS_ERROR", "message": "AI chưa thể phân tích kết quả lớp."}}) from None


@router.post("/{session_id}/checkpoints/open-all")
def open_all_checkpoints(session_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Make every generated checkpoint visible to joined students."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.open_all_checkpoints(session_id)
        return {"sessionId": session.id, "status": session.status, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None


@router.post("/{session_id}/checkpoints/close-all")
def close_all_checkpoints(session_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Hide all open checkpoints without discarding classroom evidence."""
    try:
        service.require_teacher(session_id, teacher.id)
        session = service.close_all_checkpoints(session_id, settings=AISettings.from_env())
        return {"sessionId": session.id, "status": session.status, "activeQuestionIds": session.active_question_ids}
    except SessionNotFoundError:
        raise _not_found() from None
    except LLMConfigurationError:
        raise _provider_unavailable() from None
    except LLMAuthenticationError:
        raise _provider_authentication_rejected() from None
    except LLMTimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"error": {"code": "AI_PROVIDER_TIMEOUT", "message": "AI mất quá lâu để phân tích kết quả lớp."}}) from None
    except (LLMProviderError, LLMRateLimitError, LLMMalformedResponseError, LLMValidationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": {"code": "AI_ANALYSIS_ERROR", "message": "AI chưa thể phân tích kết quả lớp."}}) from None


@router.post("/rooms/join", status_code=status.HTTP_201_CREATED)
def join_room(request: JoinRoomRequest) -> dict[str, str]:
    """Let a student join anonymously with only a room code and display name."""
    try:
        return service.join_room(request.room_code, request.display_name)
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None


@router.get("/rooms/{room_code}/state")
def room_state(room_code: str, participantId: str) -> dict[str, Any]:
    """Return the anonymous student's polling state without private class data."""
    try:
        return service.room_state(room_code, participantId)
    except SessionNotFoundError:
        raise _not_found() from None
    except SessionValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "INVALID_RESPONSE", "message": str(error)}}) from None


@router.get("/{session_id}/summary")
def get_lecturer_summary(session_id: str, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Return only aggregated evidence and a non-binding lecturer recommendation."""
    try:
        service.require_teacher(session_id, teacher.id)
        return service.summary(session_id)
    except SessionNotFoundError:
        raise _not_found() from None
