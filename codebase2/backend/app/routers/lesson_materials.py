"""Authenticated lesson upload and reuse APIs."""

from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.materials.service import MaterialUploadError, save_and_parse_upload
from app.models.material import LessonMaterial
from app.models.user import Teacher
from app.routers.auth import current_teacher

router = APIRouter(prefix="/lesson-materials", tags=["lesson materials"])
DbSession = Annotated[Session, Depends(get_db)]


def _serialize(item: LessonMaterial) -> dict:
    return {"id": item.id, "title": item.title, "filename": item.original_filename, "type": item.media_type, "status": item.status, "blockCount": len(item.source_blocks), "createdAt": item.created_at.isoformat()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_material(file: Annotated[UploadFile, File(...)], teacher: Annotated[Teacher, Depends(current_teacher)], db: DbSession, title: Annotated[str | None, Form()] = None) -> dict:
    """Store one owned PDF/PPTX and persist its source-aware extracted text."""
    try:
        material_id, filename, media_type, digest, blocks = await save_and_parse_upload(file, teacher.id)
    except MaterialUploadError as error:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_MATERIAL", "message": str(error)}}) from error
    item = LessonMaterial(id=material_id, teacher_id=teacher.id, title=(title or Path(filename).stem).strip() or "Untitled lesson", original_filename=filename, media_type=media_type, storage_key=f"{teacher.id}/{material_id}.{media_type}", sha256=digest, source_blocks=blocks)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.get("")
def list_materials(teacher: Annotated[Teacher, Depends(current_teacher)], db: DbSession) -> dict:
    """List only the authenticated teacher's reusable uploaded materials."""
    return {"materials": [_serialize(item) for item in db.scalars(select(LessonMaterial).where(LessonMaterial.teacher_id == teacher.id).order_by(LessonMaterial.created_at.desc()))]}


@router.get("/{material_id}")
def get_material(material_id: str, teacher: Annotated[Teacher, Depends(current_teacher)], db: DbSession) -> dict:
    """Return teacher-safe material metadata without disclosing its storage path."""
    item = db.scalar(select(LessonMaterial).where(LessonMaterial.id == material_id, LessonMaterial.teacher_id == teacher.id))
    if not item:
        raise HTTPException(status_code=404, detail={"error": {"code": "MATERIAL_NOT_FOUND", "message": "The lesson material was not found."}})
    return _serialize(item)
