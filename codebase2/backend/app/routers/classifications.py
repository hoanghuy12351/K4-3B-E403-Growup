"""Optional internal route for testing server-owned answer classification."""

from fastapi import APIRouter, HTTPException

from app.ai.config import AISettings
from app.ai.services.answer_classification_service import classify_explanation
from app.ai.llm.errors import LLMError
from app.domain.classification import InvalidProviderOutputError, UnknownConceptError, rubric_from_diagnostic
from app.diagnostic.repository import SessionNotFoundError
from app.routers.diagnostic_sessions import service
from app.schemas.classification import ClassificationRequest, ClassificationResponse


router = APIRouter(prefix="/classifications", tags=["classifications"])


@router.post("", response_model=ClassificationResponse, response_model_exclude_none=True)
def classify(payload: ClassificationRequest) -> ClassificationResponse:
    """Classify an existing generated question; clients never provide a rubric."""
    try:
        session = service.get_session(payload.session_id)
        section = next(item for item in session.sections if item["question"]["id"] == payload.question_id)
        decision = classify_explanation(
            rubric=rubric_from_diagnostic(section), answer=payload.answer, settings=AISettings.from_env()
        )
        return ClassificationResponse(**decision.to_dict())
    except (SessionNotFoundError, StopIteration):
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "The diagnostic session or question was not found."}}) from None
    except (UnknownConceptError, InvalidProviderOutputError, LLMError):
        raise HTTPException(status_code=502, detail={"error": {"code": "AI_PROVIDER_ERROR", "message": "The answer could not be classified safely."}}) from None
