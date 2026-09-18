"""Domain objects for analysing a server-owned multiple-choice selection.

Learners only submit an option ID. Correctness and misconception mapping are
therefore deterministic facts from the generated question, not judgements made
by an LLM.
"""

from dataclasses import dataclass


class ClassificationError(RuntimeError):
    """Base error for the answer-analysis flow."""


class UnknownConceptError(ClassificationError):
    """The requested question has no complete server-owned rubric."""


class InvalidProviderOutputError(ClassificationError):
    """The provider returned analysis that violates the grounded contract."""


@dataclass(frozen=True)
class OptionRubric:
    """One trusted option from a generated multiple-choice question."""

    id: str
    text: str
    correct: bool
    misconception_id: str | None = None


@dataclass(frozen=True)
class ConceptRubric:
    """Trusted question, options and evidence kept only on the server."""

    question_test_id: str
    concept_id: str
    question: str
    expected_evidence: tuple[str, ...]
    source_refs: tuple[str, ...]
    misconception_definitions: tuple[tuple[str, str], ...] = ()
    options: tuple[OptionRubric, ...] = ()
    citation_guidance: str = "Use only source references supplied by the server."
    review_guidance: str = "Do not infer reasoning that the learner did not submit."

    @property
    def allowed_misconceptions(self) -> frozenset[str]:
        return frozenset(item[0] for item in self.misconception_definitions)

    def option(self, option_id: str) -> OptionRubric:
        """Return a trusted option or reject an ID outside this question."""

        match = next((item for item in self.options if item.id == option_id), None)
        if match is None:
            raise UnknownConceptError("The selected option does not belong to this question.")
        return match

def rubric_from_diagnostic(section_data: dict[str, object]) -> ConceptRubric:
    """Build a private multiple-choice rubric from server-owned session data."""

    question = section_data.get("question")
    section = section_data.get("section")
    if not isinstance(question, dict) or not isinstance(section, dict):
        raise UnknownConceptError("Generated diagnostic data is incomplete.")
    raw_options = question.get("options")
    if not isinstance(raw_options, list):
        raise UnknownConceptError("Generated diagnostic question has no options.")

    options = tuple(
        OptionRubric(
            id=str(item.get("id", "")),
            text=str(item.get("text", "")),
            correct=bool(item.get("correct")),
            misconception_id=str(item["misconceptionId"]) if item.get("misconceptionId") else None,
        )
        for item in raw_options
        if isinstance(item, dict) and item.get("id") and item.get("text")
    )
    correct_options = [item for item in options if item.correct]
    if len(correct_options) != 1:
        raise UnknownConceptError("Generated diagnostic question must have exactly one correct option.")

    misconception_items = section_data.get("misconceptions")
    definitions = tuple(
        (str(item.get("id")), str(item.get("statement")))
        for item in misconception_items if isinstance(item, dict) and item.get("id") and item.get("statement")
    ) if isinstance(misconception_items, list) else ()

    # Question sources use `id`; segmented lesson sources use `sourceId`.
    raw_refs: list[object] = []
    if isinstance(question.get("source"), list):
        raw_refs.extend(question["source"])
    if isinstance(section.get("sourceRefs"), list):
        raw_refs.extend(section["sourceRefs"])
    refs = tuple(dict.fromkeys(
        str(item.get("id") or item.get("sourceId"))
        for item in raw_refs
        if isinstance(item, dict) and (item.get("id") or item.get("sourceId"))
    ))

    return ConceptRubric(
        question_test_id=str(question.get("id", "")),
        concept_id=str(question.get("concept", "")),
        question=str(question.get("question", "")),
        expected_evidence=tuple(item.text for item in correct_options),
        source_refs=refs,
        misconception_definitions=definitions,
        options=options,
    )
