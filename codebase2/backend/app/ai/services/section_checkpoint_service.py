"""Generate exactly one checkpoint from one already-isolated section bundle."""

from dataclasses import dataclass
from typing import Any

from ..config import AISettings
from ..llm.errors import LLMError
from ..services.concept_extractor import extract_concepts
from ..services.llm_diagnostic_service import generate_llm_diagnostic
from ..services.question_generator import generate_diagnostic_question
from ..validation import validate_diagnostic_question
from .section_evidence import SectionEvidence


@dataclass(frozen=True)
class SectionCheckpoint:
    """A single session-compatible checkpoint generated for one section only."""

    section: dict[str, Any]
    concepts: list[str]
    learning_objectives: list[str]
    misconceptions: list[dict[str, Any]]
    historical_evidence: dict[str, Any]
    question: dict[str, Any]
    generation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the checkpoint using the existing session section shape."""
        return {
            "sectionId": self.section["id"],
            "section": self.section,
            "concepts": self.concepts,
            "learningObjectives": self.learning_objectives,
            "misconceptions": self.misconceptions,
            "historicalEvidence": self.historical_evidence,
            "question": self.question,
            "generation": self.generation,
        }


def _evidence_text(evidence: SectionEvidence) -> str:
    """Combine only selected evidence for local deterministic generation."""
    slides = "\n".join(str(item["text"]) for item in evidence.slide_evidence)
    transcript = "\n".join(item["text"] for item in evidence.transcript_evidence)
    return f"Slide evidence:\n{slides}\n\nLecturer transcript evidence:\n{transcript}"


def _generation_metadata(mode: str, *, fallback_used: bool = False, fallback_reason: str | None = None) -> dict[str, Any]:
    """Keep response metadata consistent without returning prompt or evidence text."""
    return {
        "mode": mode,
        "provider": None,
        "model": None,
        "latencyMs": 0,
        "fallbackUsed": fallback_used,
        "fallbackReason": fallback_reason,
        "retryCount": 0,
        "usage": None,
    }


def _deterministic_checkpoint(evidence: SectionEvidence, context: dict[str, Any], *, fallback_used: bool = False, fallback_reason: str | None = None) -> SectionCheckpoint:
    """Create one local question while retaining the same selected evidence boundary."""
    teaching_context = _teaching_context(evidence)
    question = generate_diagnostic_question(concept_context=context, misconceptions=[], source_context=teaching_context)
    question["id"] = f"Q-{evidence.section_id}"
    question["source"] = evidence.source_refs
    validation = validate_diagnostic_question(question)
    if not validation["valid"]:
        raise ValueError(f"Generated diagnostic question is invalid: {' '.join(validation['errors'])}")
    return SectionCheckpoint(
        section={"id": evidence.section_id, "title": evidence.title, "order": 1, "sourceRefs": evidence.source_refs},
        concepts=list(context["concepts"]),
        learning_objectives=list(context["learningObjectives"]),
        misconceptions=[],
        historical_evidence={"matchedQuestions": 0},
        question=question,
        generation=_generation_metadata("deterministic", fallback_used=fallback_used, fallback_reason=fallback_reason),
    )


def _teaching_context(evidence: SectionEvidence) -> dict[str, Any]:
    """Make explicit evidence channels available to the unified provider layer."""
    return {
        "title": evidence.title,
        "text": _evidence_text(evidence),
        "sourceId": evidence.lesson_id,
        "sourceType": "pdf_page",
        "allowedSourceRefs": evidence.source_refs,
        "slideEvidence": evidence.slide_evidence,
        "transcriptEvidence": evidence.transcript_evidence,
        "sectionId": evidence.section_id,
    }


def generate_checkpoint_for_section(section_evidence: SectionEvidence, settings: AISettings | None = None) -> SectionCheckpoint:
    """Generate one and only one checkpoint without lesson-wide orchestration."""
    settings = settings or AISettings.from_env()
    teaching_context = _teaching_context(section_evidence)
    context = extract_concepts(
        source_text=teaching_context["text"],
        title=section_evidence.title,
        source_id=section_evidence.lesson_id,
    )
    if settings.mode == "deterministic":
        return _deterministic_checkpoint(section_evidence, context)
    try:
        result, generation = generate_llm_diagnostic(
            teaching_context=teaching_context,
            concept_seed=context,
            historical_questions=[],
            settings=settings,
        )
    except LLMError as error:
        if settings.mode == "hybrid" and settings.fallback_to_deterministic:
            return _deterministic_checkpoint(section_evidence, context, fallback_used=True, fallback_reason=str(error))
        raise
    question = result.question.model_dump()
    question["id"] = f"Q-{section_evidence.section_id}"
    question["source"] = section_evidence.source_refs
    return SectionCheckpoint(
        section={"id": section_evidence.section_id, "title": section_evidence.title, "order": 1, "sourceRefs": section_evidence.source_refs},
        concepts=list(result.concepts),
        learning_objectives=[result.learningObjective],
        misconceptions=[item.model_dump() for item in result.misconceptions],
        historical_evidence={"matchedQuestions": 0},
        question=question,
        generation=generation,
    )
