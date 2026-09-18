"""Generate one canonical diagnostic question for each lesson section."""

from dataclasses import dataclass
import logging
from typing import Any

from ..config import AISettings
from ..pipeline import generate_diagnostic_check
from .lesson_segmenter import LessonSection, segment_lesson
from .material_ingestion import IngestedMaterial

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SectionDiagnostic:
    """Section-scoped AI result retained by the session workflow."""

    section: LessonSection
    concepts: list[str]
    learning_objectives: list[str]
    misconceptions: list[dict[str, Any]]
    historical_evidence: dict[str, Any]
    question: dict[str, Any]
    generation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize a section result without removing pipeline metadata."""
        return {
            "sectionId": self.section.id,
            "section": self.section.to_dict(),
            "concepts": self.concepts,
            "learningObjectives": self.learning_objectives,
            "misconceptions": self.misconceptions,
            "historicalEvidence": self.historical_evidence,
            "question": self.question,
            "generation": self.generation,
        }


def generate_lesson_diagnostic(material: IngestedMaterial, *, options: dict[str, Any] | None = None, settings: AISettings | None = None) -> list[SectionDiagnostic]:
    """Orchestrate the existing one-question pipeline once per segmented lesson section."""
    settings = settings or AISettings.from_env()
    diagnostics: list[SectionDiagnostic] = []
    for section in segment_lesson(material):
        teaching_context = {
            "title": section.title,
            "text": section.text,
            "sourceId": material.source_id,
            "sourceType": section.source_refs[0]["type"],
        }
        try:
            result = generate_diagnostic_check(teaching_context=teaching_context, options=options or {}, settings=settings)
        except Exception as error:
            logger.warning(
                "Diagnostic generation failed: sectionId=%s sectionTitle=%s error=%s: %s",
                section.id,
                section.title,
                type(error).__name__,
                str(error),
            )
            raise
        context = result["context"]
        question = dict((result.get("questions") or [])[0])
        question["id"] = f"Q-{section.id}"
        question["source"] = [{"type": teaching_context["sourceType"], "id": material.source_id}]
        diagnostics.append(
            SectionDiagnostic(
                section=section,
                concepts=list(context.get("concepts") or []),
                learning_objectives=list(context.get("learningObjectives") or []),
                misconceptions=list(result.get("misconceptions") or []),
                historical_evidence=dict(result.get("historicalEvidence") or {}),
                question=question,
                generation=dict(result.get("generation") or {}),
            )
        )
    return diagnostics
