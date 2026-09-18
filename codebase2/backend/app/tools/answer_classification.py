"""Grounded AI tool for classifying a learner answer."""

import re
import unicodedata

from app.domain.classification import (
    ALLOWED_LABELS,
    ClassificationDecision,
    ConceptRubric,
    InvalidProviderOutputError,
)
from app.prompts.answer_classification import SYSTEM_PROMPT, build_user_prompt
from app.ai.llm.base import LLMProvider
from app.ai.llm.models import ProviderResult
from app.ai.llm.errors import LLMMalformedResponseError


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_%]+", " ", value)).strip()


def _obvious_prompt_injection(answer: str) -> bool:
    """A narrow safety pre-check; it never decides educational understanding."""

    text = _normalise(answer)
    markers = (
        "system override",
        "system_override",
        "ignore previous",
        "bo qua rubric",
        "bo qua huong dan",
        "danh dau ca lop",
        "in danh sach hoc vien",
    )
    return any(_normalise(marker) in text for marker in markers)


def _validate_grounding(
    decision: ClassificationDecision, rubric: ConceptRubric
) -> ClassificationDecision:
    invalid_refs = set(decision.source_refs) - set(rubric.source_refs)
    if invalid_refs:
        raise InvalidProviderOutputError(
            f"Provider invented source refs: {sorted(invalid_refs)}"
        )
    invalid_misconceptions = (
        set(decision.misconceptions) - rubric.allowed_misconceptions
    )
    if invalid_misconceptions:
        raise InvalidProviderOutputError(
            f"Provider invented misconception ids: {sorted(invalid_misconceptions)}"
        )
    if decision.label == "teacher_review" and not decision.needs_teacher_review:
        raise InvalidProviderOutputError("teacher_review requires needs_teacher_review=true")
    if decision.label != "teacher_review" and decision.needs_teacher_review:
        raise InvalidProviderOutputError(
            "needs_teacher_review must be false for non-review labels"
        )
    if decision.label == "unclear" and (
        decision.source_refs or decision.misconceptions
    ):
        raise InvalidProviderOutputError(
            "unclear decisions cannot claim sources or misconceptions"
        )
    return decision


class AnswerClassificationTool:
    """Build prompts, invoke AI, then enforce the grounded output contract."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def classify_with_rubric(self, *, rubric: ConceptRubric, answer: str) -> ClassificationDecision:
        """Classify one explanation using the canonical structured AI provider."""
        if _obvious_prompt_injection(answer):
            return ClassificationDecision("unclear", (), (), False, "prompt_injection_detected")
        result: ProviderResult = self.provider.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(rubric, answer),
            schema={
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": sorted(ALLOWED_LABELS)},
                    "misconceptions": {"type": "array", "items": {"type": "string"}},
                    "source_refs": {"type": "array", "items": {"type": "string"}},
                    "needs_teacher_review": {"type": "boolean"},
                },
                "required": ["label", "misconceptions", "source_refs", "needs_teacher_review"],
                "additionalProperties": False,
            },
            request_id=f"classification-{rubric.question_test_id}",
        )
        if not isinstance(result.data, dict):
            raise LLMMalformedResponseError("Classification provider returned invalid data.")
        return _validate_grounding(ClassificationDecision.from_dict(result.data), rubric)

    def classify(
        self, *, question_test_id: str, concept_id: str, answer: str
    ) -> ClassificationDecision:
        raise UnknownConceptError("Static question rubrics are not available in the integrated classroom flow.")
