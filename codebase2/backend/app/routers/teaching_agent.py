"""Teacher-only endpoints for the fixed, section-scoped checkpoint demo."""

import logging
from pathlib import Path

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.ai.services.demo_checkpoint_catalog import DemoCheckpointCatalogError, get_demo_section, load_demo_catalog
from app.ai.config import AISettings, find_repository_root
from app.ai.llm.errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, LLMValidationError
from app.ai.services.demo_slide_analysis import generate_preanalyzed_checkpoints, get_preanalyzed_section
from app.diagnostic.service import SessionValidationError
from app.models.user import Teacher
from app.routers.auth import current_teacher
from app.routers.diagnostic_sessions import service
from app.schemas.teaching_agent import CreateLiveSessionRequest, GenerateAgentCheckpointRequest, GenerateDemoCheckpointRequest


router = APIRouter(prefix="/teaching-agent", tags=["Teaching agent"])
logger = logging.getLogger(__name__)


def _error(status_code: int, code: str, message: str) -> HTTPException:
    """Return a stable error without local paths, evidence text, or provider bodies."""
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message}})


def _configured_model(settings: AISettings | None) -> str:
    """Select a safe model label for logs without reading provider request data."""
    if settings is None:
        return "unknown"
    return str(getattr(settings, f"{settings.provider}_model", None) or "unknown")


@router.get("/live-lesson/slides")
def get_live_lesson_slides(teacher: Annotated[Teacher, Depends(current_teacher)]) -> FileResponse:
    """Stream the canonical slide deck for the lecturer's live presentation view."""
    del teacher
    try:
        lesson = load_demo_catalog()["lesson"]
        slide_file = lesson["slideFile"]
        slide_path = (find_repository_root() / str(slide_file)).resolve()
        data_root = (find_repository_root() / "data").resolve()
        slide_path.relative_to(data_root)
    except (DemoCheckpointCatalogError, KeyError, TypeError, ValueError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_SLIDES_UNAVAILABLE", "Live lesson slides are unavailable.") from None
    if not slide_path.is_file():
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_SLIDES_UNAVAILABLE", "Live lesson slides are unavailable.")
    return FileResponse(slide_path, media_type="application/pdf", filename="ai-llm-foundation.pdf", content_disposition_type="inline")


@router.get("/demo")
def get_demo(teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Ask an authenticated teacher to select a fixed conceptual lesson section."""
    del teacher
    try:
        catalog = load_demo_catalog()
        lesson = catalog["lesson"]
        sections = catalog["sections"]
    except (DemoCheckpointCatalogError, KeyError, TypeError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_CATALOG_UNAVAILABLE", "Preset demo data is unavailable.") from None
    return {
        "lesson": {"id": lesson["id"], "title": lesson["title"]},
        "agentMessage": catalog["agentMessage"],
        "sections": [
            {
                "id": section["id"],
                "title": section["title"],
                "order": section["order"],
                "slidePages": section["slidePages"],
                "triggerSlide": max(section["slidePages"]),
                "concepts": get_preanalyzed_section(section["id"])["concepts"],
                "learningObjectives": get_preanalyzed_section(section["id"])["learningObjectives"],
                "misconceptions": get_preanalyzed_section(section["id"])["misconceptions"],
            }
            for section in sections
        ],
        "mode": "preset_demo",
    }


@router.post("/live-session", status_code=status.HTTP_201_CREATED)
def create_live_session(request: CreateLiveSessionRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Create a multi-checkpoint live lesson plan without generating questions yet."""
    try:
        session = service.create_live_session(
            teacher_id=teacher.id,
            lesson_id=request.lesson_id,
            expected_students=request.expected_students,
            selections=[item.model_dump(by_alias=True, exclude_none=True) for item in request.checkpoint_selections],
        )
    except SessionValidationError as error:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_LIVE_PLAN", str(error)) from None
    return {
        "sessionId": session.id,
        "roomCode": session.room_code,
        "status": session.status,
        "lesson": {"id": session.lesson["id"], "title": session.lesson["title"]},
        "checkpointPlans": session.checkpoint_plans,
    }


@router.post("/demo/checkpoints", status_code=status.HTTP_201_CREATED)
def generate_demo_checkpoint(request: GenerateDemoCheckpointRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Create one prepared checkpoint session without runtime AI or source parsing."""
    try:
        get_demo_section(request.section_id)
        session = service.create_preset_demo_session(
            teacher_id=teacher.id,
            section_id=request.section_id,
            expected_students=request.expected_students,
        )
    except KeyError:
        raise _error(status.HTTP_404_NOT_FOUND, "DEMO_SECTION_NOT_FOUND", "The requested demo section was not found.") from None
    except (DemoCheckpointCatalogError, SessionValidationError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_CATALOG_UNAVAILABLE", "Preset demo data is unavailable.") from None
    checkpoints = [
        {
            "id": item["question"]["id"],
            "concept": item["question"]["concept"],
            "question": item["question"]["question"],
            "options": item["question"]["options"],
            "sourceRefs": [source["id"] for source in item["question"]["source"]],
        }
        for item in session.sections
    ]
    return {
        "sessionId": session.id,
        "roomCode": session.room_code,
        "status": session.status,
        "lesson": {"id": session.lesson["id"], "title": session.lesson["title"]},
        "selectedSection": {"id": request.section_id, "title": get_demo_section(request.section_id)["title"]},
        "checkpoint": checkpoints[0],
        "checkpoints": checkpoints,
        "generation": session.sections[0]["generation"],
    }


@router.post("/demo/generate", status_code=status.HTTP_201_CREATED)
def generate_agent_checkpoints(request: GenerateAgentCheckpointRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Create a draft from provider-generated questions grounded in demo analysis."""
    settings: AISettings | None = None
    try:
        analysis = get_preanalyzed_section(request.section_id)
        settings = AISettings.from_env()
        sections, generation = generate_preanalyzed_checkpoints(
            analysis=analysis,
            teacher_request=request.teacher_request,
            settings=settings,
        )
        session = service.create_agent_demo_session(
            teacher_id=teacher.id,
            analysis=analysis,
            sections=sections,
            expected_students=request.expected_students,
        )
    except KeyError:
        raise _error(status.HTTP_404_NOT_FOUND, "DEMO_SECTION_NOT_FOUND", "The requested demo section was not found.") from None
    except LLMConfigurationError as error:
        logger.warning("Teaching Agent generation failed: provider=%s model=%s section=%s error=%s", settings.provider if settings else "unknown", _configured_model(settings), request.section_id, type(error).__name__)
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "AI_PROVIDER_CONFIGURATION_ERROR", "Teaching Agent question generation requires an LLM provider.") from None
    except LLMAuthenticationError as error:
        logger.warning("Teaching Agent generation failed: provider=%s model=%s section=%s error=%s", settings.provider if settings else "unknown", _configured_model(settings), request.section_id, type(error).__name__)
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "AI_PROVIDER_AUTHENTICATION_ERROR", "The configured AI provider rejected the server credentials.") from None
    except LLMTimeoutError as error:
        logger.warning("Teaching Agent generation failed: provider=%s model=%s section=%s error=%s", settings.provider if settings else "unknown", _configured_model(settings), request.section_id, type(error).__name__)
        raise _error(status.HTTP_504_GATEWAY_TIMEOUT, "AI_PROVIDER_TIMEOUT", "The AI provider took too long to create checkpoints.") from None
    except (LLMProviderError, LLMRateLimitError) as error:
        logger.warning("Teaching Agent generation failed: provider=%s model=%s section=%s error=%s", settings.provider if settings else "unknown", _configured_model(settings), request.section_id, type(error).__name__)
        raise _error(status.HTTP_502_BAD_GATEWAY, "AI_PROVIDER_ERROR", "The configured AI provider could not create checkpoints.") from None
    except (LLMMalformedResponseError, LLMValidationError) as error:
        logger.warning("Teaching Agent generation returned invalid output: provider=%s model=%s section=%s error=%s", settings.provider if settings else "unknown", _configured_model(settings), request.section_id, type(error).__name__)
        raise _error(status.HTTP_502_BAD_GATEWAY, "AI_OUTPUT_INVALID", "The AI returned a checkpoint in an invalid format. Please generate again.") from None
    except (DemoCheckpointCatalogError, SessionValidationError, TypeError, ValueError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_CATALOG_UNAVAILABLE", "Pre-analyzed demo data is unavailable.") from None
    checkpoints = []
    for item in session.sections:
        question = item["question"]
        checkpoints.append({
            "id": question["id"],
            "sectionId": item["section"]["id"],
            "originalSectionId": item["section"].get("originalSectionId", analysis["section"]["id"]),
            "concept": question["concept"],
            "question": question["question"],
            "learningObjective": question["learningObjective"],
            "options": [{"id": option["id"], "text": option["text"]} for option in question["options"]],
            "sourceRefs": item["section"]["sourceRefs"],
        })
    return {
        "agentMessage": f"Em đã tạo {len(checkpoints)} checkpoint cho phần {analysis['section']['title']} theo yêu cầu của thầy/cô.",
        "sessionId": session.id,
        "roomCode": session.room_code,
        "status": session.status,
        "lesson": analysis["lesson"],
        "selectedSection": {"id": analysis["section"]["id"], "title": analysis["section"]["title"]},
        "teacherRequest": request.teacher_request,
        "checkpoints": checkpoints,
        "generation": generation,
    }
