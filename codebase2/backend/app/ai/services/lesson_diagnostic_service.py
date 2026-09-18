"""Generate one canonical diagnostic question for each lesson section."""

from dataclasses import dataclass
from typing import Any

from ..config import AISettings
from ..pipeline import generate_diagnostic_check
from .lesson_segmenter import LessonSection, segment_lesson
from .material_ingestion import IngestedMaterial


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
        result = generate_diagnostic_check(
            teaching_context={"title": section.title, "text": section.text, "sourceId": f"{material.source_id}:{section.id}"},
            options=options or {},
            settings=settings,
        )
        context = result["context"]
        diagnostics.append(
            SectionDiagnostic(
                section=section,
                concepts=list(context.get("concepts") or []),
                learning_objectives=list(context.get("learningObjectives") or []),
                misconceptions=list(result.get("misconceptions") or []),
                historical_evidence=dict(result.get("historicalEvidence") or {}),
                question=dict((result.get("questions") or [])[0]),
                generation=dict(result.get("generation") or {}),
            )
        )
    return diagnostics
