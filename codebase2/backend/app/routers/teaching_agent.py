"""Teacher-only endpoints for the fixed, section-scoped checkpoint demo."""

import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.config import AISettings
from app.ai.data.demo_lesson_catalog import DemoLessonCatalogError, get_demo_lesson
from app.ai.llm.errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, LLMValidationError
from app.ai.services.section_checkpoint_service import generate_checkpoint_for_section
from app.ai.services.section_evidence import build_section_evidence
from app.ai.services.slide_evidence import SlideEvidenceError
from app.ai.services.transcript_ingestion import TranscriptIngestionError
from app.models.user import Teacher
from app.routers.auth import current_teacher
from app.routers.diagnostic_sessions import service
from app.schemas.teaching_agent import GenerateDemoCheckpointRequest


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teaching-agent", tags=["Teaching agent"])


def _error(status_code: int, code: str, message: str) -> HTTPException:
    """Return a stable error without local paths, evidence text, or provider bodies."""
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message}})


@router.get("/demo")
def get_demo(teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Ask an authenticated teacher to select a fixed conceptual lesson section."""
    del teacher
    try:
        lesson = get_demo_lesson()
    except DemoLessonCatalogError:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "SECTION_EVIDENCE_UNAVAILABLE", "Demo lesson evidence is unavailable.") from None
    return {
        "lesson": {"id": lesson.id, "title": lesson.title},
        "agentMessage": "Bạn muốn tạo checkpoint cho phần nào?",
        "sections": [{"id": section.id, "title": section.title} for section in lesson.sections],
    }


@router.post("/demo/checkpoints", status_code=status.HTTP_201_CREATED)
def generate_demo_checkpoint(request: GenerateDemoCheckpointRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Generate one isolated checkpoint and save it in the normal session workflow."""
    try:
        lesson = get_demo_lesson()
        evidence = build_section_evidence(request.section_id)
    except KeyError:
        raise _error(status.HTTP_404_NOT_FOUND, "DEMO_SECTION_NOT_FOUND", "The requested demo section was not found.") from None
    except DemoLessonCatalogError:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "SECTION_EVIDENCE_INVALID", "Demo lesson alignment is invalid.") from None
    except (SlideEvidenceError, TranscriptIngestionError, OSError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "SECTION_EVIDENCE_UNAVAILABLE", "Selected section evidence is unavailable.") from None
    try:
        checkpoint = generate_checkpoint_for_section(evidence, settings=AISettings.from_env()).to_dict()
        session = service.create_section_session(
            lesson={
                "id": lesson.id,
                "title": lesson.title,
                "sourceId": lesson.id,
                "slideSource": Path(lesson.slide_path).name,
                "transcriptSource": Path(lesson.transcript_path).name,
            },
            checkpoint=checkpoint,
            expected_students=request.expected_students,
            teacher_id=teacher.id,
        )
    except LLMConfigurationError:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "AI_PROVIDER_CONFIGURATION_ERROR", "The configured AI provider requires valid credentials and model configuration.") from None
    except LLMAuthenticationError:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "AI_PROVIDER_AUTHENTICATION_ERROR", "The configured AI provider rejected the server credentials.") from None
    except LLMTimeoutError:
        raise _error(status.HTTP_504_GATEWAY_TIMEOUT, "AI_PROVIDER_TIMEOUT", "The AI provider timed out while generating the checkpoint.") from None
    except (LLMProviderError, LLMRateLimitError, LLMMalformedResponseError, LLMValidationError):
        logger.warning("Demo checkpoint generation failed: lessonId=%s sectionId=%s", lesson.id, request.section_id)
        raise _error(status.HTTP_502_BAD_GATEWAY, "AI_PROVIDER_ERROR", "The configured AI provider could not generate the checkpoint.") from None
    section = checkpoint["section"]
    question = checkpoint["question"]
    return {
        "sessionId": session.id,
        "roomCode": session.room_code,
        "status": session.status,
        "lesson": {"id": lesson.id, "title": lesson.title},
        "selectedSection": {"id": section["id"], "title": section["title"]},
        "checkpoint": {
            "id": question["id"],
            "concept": question["concept"],
            "question": question["question"],
            "options": question["options"],
            "sourceRefs": [item["id"] for item in question["source"]],
        },
    }
