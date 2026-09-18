"""Expose bounded, pre-analyzed evidence for the fixed Teaching Agent demo."""

from typing import Any

from app.ai.config import AISettings
from app.ai.services.llm_checkpoint_batch_service import generate_llm_checkpoint_batch

from .demo_checkpoint_catalog import DemoCheckpointCatalogError, _section_source_refs, get_demo_checkpoint, get_demo_section, load_demo_catalog


def get_preanalyzed_section(section_id: str) -> dict[str, Any]:
    """Return selected slide-analysis data without loading PDFs or transcripts at runtime."""
    section = get_demo_section(section_id)
    checkpoint = get_demo_checkpoint(section_id)
    lesson = load_demo_catalog().get("lesson")
    if not isinstance(lesson, dict):
        raise DemoCheckpointCatalogError("Preset demo lesson metadata is invalid.")
    question = checkpoint.get("question")
    if not isinstance(question, dict) or not isinstance(question.get("source"), list):
        raise DemoCheckpointCatalogError("Preset demo analysis has invalid source references.")
    allowed_refs = _section_source_refs(section, question["source"])
    concepts = checkpoint.get("concepts")
    objectives = checkpoint.get("learningObjectives")
    misconceptions = checkpoint.get("misconceptions")
    if not all(isinstance(value, list) for value in (concepts, objectives, misconceptions)):
        raise DemoCheckpointCatalogError("Preset demo analysis is incomplete.")
    return {
        "lesson": {"id": lesson["id"], "title": lesson["title"]},
        "section": {"id": section["id"], "title": section["title"], "order": section["order"], "slidePages": section["slidePages"]},
        "concepts": concepts,
        "learningObjectives": objectives,
        "misconceptions": misconceptions,
        "allowedSourceRefs": allowed_refs,
    }


def generate_preanalyzed_checkpoints(*, analysis: dict[str, Any], teacher_request: str, settings: AISettings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Generate a validated batch without mock fallbacks or repeated provider calls."""
    batch, generation = generate_llm_checkpoint_batch(analysis=analysis, teacher_request=teacher_request, settings=settings)
    sections = []
    for index, question in enumerate(batch.questions, start=1):
        question_data = question.model_dump()
        question_id = f"{analysis['section']['id']}-q{index:02d}"
        question_data["id"] = question_id
        sections.append({
            "sectionId": question_id,
            "section": {
                "id": question_id,
                "originalSectionId": analysis["section"]["id"],
                "title": f"{analysis['section']['title']} — Câu {index}",
                "order": index,
                "sourceRefs": analysis["allowedSourceRefs"],
            },
            "concepts": analysis["concepts"],
            "learningObjectives": analysis["learningObjectives"],
            "misconceptions": analysis["misconceptions"],
            "historicalEvidence": {"matchedQuestions": 0},
            "question": question_data,
            "generation": generation,
        })
    return sections, generation
