"""Teacher-only endpoints for the fixed, section-scoped checkpoint demo."""

import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.services.demo_checkpoint_catalog import DemoCheckpointCatalogError, get_demo_section, load_demo_catalog
from app.diagnostic.service import SessionValidationError
from app.models.user import Teacher
from app.routers.auth import current_teacher
from app.routers.diagnostic_sessions import service
from app.schemas.teaching_agent import GenerateDemoCheckpointRequest


router = APIRouter(prefix="/teaching-agent", tags=["Teaching agent"])
DEMO_PROCESS_DELAY_SECONDS = 30


def _error(status_code: int, code: str, message: str) -> HTTPException:
    """Return a stable error without local paths, evidence text, or provider bodies."""
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message}})


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
        "sections": [{"id": section["id"], "title": section["title"]} for section in sections],
        "mode": "preset_demo",
    }


@router.post("/demo/checkpoints", status_code=status.HTTP_201_CREATED)
def generate_demo_checkpoint(request: GenerateDemoCheckpointRequest, teacher: Annotated[Teacher, Depends(current_teacher)]) -> dict[str, Any]:
    """Create one prepared checkpoint session without runtime AI or source parsing."""
    try:
        get_demo_section(request.section_id)
        time.sleep(DEMO_PROCESS_DELAY_SECONDS)
        session = service.create_preset_demo_session(
            teacher_id=teacher.id,
            section_id=request.section_id,
            expected_students=request.expected_students,
        )
    except KeyError:
        raise _error(status.HTTP_404_NOT_FOUND, "DEMO_SECTION_NOT_FOUND", "The requested demo section was not found.") from None
    except (DemoCheckpointCatalogError, SessionValidationError):
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "DEMO_CATALOG_UNAVAILABLE", "Preset demo data is unavailable.") from None
    checkpoint = session.sections[0]
    section = checkpoint["section"]
    question = checkpoint["question"]
    return {
        "sessionId": session.id,
        "roomCode": session.room_code,
        "status": session.status,
        "lesson": {"id": session.lesson["id"], "title": session.lesson["title"]},
        "selectedSection": {"id": section["id"], "title": section["title"]},
        "checkpoint": {
            "id": question["id"],
            "concept": question["concept"],
            "question": question["question"],
            "options": question["options"],
            "sourceRefs": [item["id"] for item in question["source"]],
        },
        "generation": checkpoint["generation"],
    }
