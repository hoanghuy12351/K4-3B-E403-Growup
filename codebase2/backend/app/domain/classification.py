"""Provider-neutral classification domain objects."""

from dataclasses import dataclass
from typing import Literal


Label = Literal["understood", "partial", "misunderstood", "unclear", "teacher_review"]
ALLOWED_LABELS = frozenset(
    {"understood", "partial", "misunderstood", "unclear", "teacher_review"}
)


class ClassificationError(RuntimeError):
    """Base error for the AI classification flow."""


class UnknownConceptError(ClassificationError):
    """The requested question/concept pair has no server-owned rubric."""


class InvalidProviderOutputError(ClassificationError):
    """The provider returned content that violates the grounded contract."""


@dataclass(frozen=True)
class ClassificationDecision:
    label: Label
    misconceptions: tuple[str, ...]
    source_refs: tuple[str, ...]
    needs_teacher_review: bool
    security_event: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ClassificationDecision":
        label = payload.get("label")
        misconceptions = payload.get("misconceptions")
        source_refs = payload.get("source_refs")
        needs_review = payload.get("needs_teacher_review")
        security_event = payload.get("security_event")
        if label not in ALLOWED_LABELS:
            raise InvalidProviderOutputError(f"Invalid label from provider: {label!r}")
        if not isinstance(misconceptions, list) or not all(
            isinstance(item, str) for item in misconceptions
        ):
            raise InvalidProviderOutputError("misconceptions must be a string array")
        if not isinstance(source_refs, list) or not all(
            isinstance(item, str) for item in source_refs
        ):
            raise InvalidProviderOutputError("source_refs must be a string array")
        if not isinstance(needs_review, bool):
            raise InvalidProviderOutputError("needs_teacher_review must be boolean")
        if security_event not in {None, "prompt_injection_detected"}:
            raise InvalidProviderOutputError("Invalid security_event from provider")
        return cls(
            label=label,  # type: ignore[arg-type]
            misconceptions=tuple(misconceptions),
            source_refs=tuple(source_refs),
            needs_teacher_review=needs_review,
            security_event=security_event,  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "label": self.label,
            "misconceptions": list(self.misconceptions),
            "source_refs": list(self.source_refs),
            "needs_teacher_review": self.needs_teacher_review,
        }
        if self.security_event is not None:
            result["security_event"] = self.security_event
        return result


@dataclass(frozen=True)
class ConceptRubric:
    question_test_id: str
    concept_id: str
    question: str
    expected_evidence: tuple[str, ...]
    source_refs: tuple[str, ...]
    misconception_definitions: tuple[tuple[str, str], ...] = ()
    citation_guidance: str = "Use every directly relevant source reference."
    review_guidance: str = "Escalate only when the supplied sources are conflicting or insufficient."

    @property
    def allowed_misconceptions(self) -> frozenset[str]:
        return frozenset(item[0] for item in self.misconception_definitions)


def rubric_from_diagnostic(section_data: dict[str, object]) -> ConceptRubric:
    """Build a private rubric from a generated server-owned diagnostic section."""
    question = section_data.get("question")
    section = section_data.get("section")
    if not isinstance(question, dict) or not isinstance(section, dict):
        raise UnknownConceptError("Generated diagnostic data is incomplete.")
    options = question.get("options")
    if not isinstance(options, list):
        raise UnknownConceptError("Generated diagnostic question has no options.")
    expected = tuple(str(option.get("text", "")) for option in options if isinstance(option, dict) and option.get("correct"))
    if not expected:
        raise UnknownConceptError("Generated diagnostic question has no answer evidence.")
    misconceptions = section_data.get("misconceptions")
    misconception_items = misconceptions if isinstance(misconceptions, list) else []
    definitions = tuple(
        (str(item.get("id")), str(item.get("statement")))
        for item in misconception_items if isinstance(item, dict) and item.get("id") and item.get("statement")
    )
    refs = tuple(str(item.get("id")) for item in section.get("sourceRefs", []) if isinstance(item, dict) and item.get("id"))
    return ConceptRubric(
        question_test_id=str(question.get("id", "")),
        concept_id=str(question.get("concept", "")),
        question=str(question.get("question", "")),
        expected_evidence=expected,
        source_refs=refs,
        misconception_definitions=definitions,
    )
