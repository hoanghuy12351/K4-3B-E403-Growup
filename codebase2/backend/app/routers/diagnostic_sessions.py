"""FastAPI routes for lecturer and student diagnostic-session workflows."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.ai import AISettings
from app.ai.llm.errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, LLMValidationError
from app.ai.services.material_ingestion import MaterialIngestionError, list_available_materials
from app.diagnostic.repository import InMemoryDiagnosticSessionRepository, SessionNotFoundError
from app.diagnostic.service import DiagnosticSessionService, SessionValidationError
from app.schemas.diagnostic_session import CreateDiagnosticSessionRequest, StudentResponseRequest

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
def get_lesson_materials() -> dict[str, list[dict[str, str]]]:
    """Return selectable PDF lessons discovered from the repository data directory."""
    try:
        return {"materials": [item.to_dict() for item in list_available_materials()]}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "MATERIAL_DATA_UNAVAILABLE", "message": "Local lesson material is unavailable."}}) from None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(request: CreateDiagnosticSessionRequest) -> dict[str, Any]:
    """Create a lecturer-reviewable draft with one generated question per section."""
    try:
        session = service.create_session(
            lesson=request.lesson.model_dump(by_alias=True, exclude_none=True),
            expected_students=request.expected_students,
            settings=AISettings.from_env(),
        )
        return {
            "sessionId": session.id,
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
def start_session(session_id: str) -> dict[str, str]:
    """Allow the lecturer to mark a reviewed draft as active for students."""
    try:
        session = service.start_session(session_id)
        return {"sessionId": session.id, "status": session.status}
    except SessionNotFoundError:
        raise _not_found() from None


@router.get("/{session_id}")
def get_student_session(session_id: str) -> dict[str, Any]:
    """Return student-safe questions without answer keys or other responses."""
    try:
        return service.student_view(service.get_session(session_id))
    except SessionNotFoundError:
        raise _not_found() from None


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


@router.get("/{session_id}/summary")
def get_lecturer_summary(session_id: str) -> dict[str, Any]:
    """Return only aggregated evidence and a non-binding lecturer recommendation."""
    try:
        return service.summary(session_id)
    except SessionNotFoundError:
        raise _not_found() from None
