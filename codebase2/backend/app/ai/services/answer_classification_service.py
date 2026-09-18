"""Classification orchestration using the shared structured LLM provider layer."""

from app.ai.config import AISettings
from app.ai.llm.factory import create_provider
from app.domain.classification import ClassificationDecision, ConceptRubric
from app.tools.answer_classification import AnswerClassificationTool


def classify_explanation(*, rubric: ConceptRubric, explanation: str, settings: AISettings) -> ClassificationDecision:
    """Use a deterministic fallback when configured AI is unavailable for this prototype."""
    if not explanation.strip():
        return ClassificationDecision("unclear", (), (), False)
    if settings.mode == "deterministic":
        text = explanation.casefold()
        expected_matches = sum(1 for evidence in rubric.expected_evidence if evidence.casefold()[:24] in text)
        label = "understood" if expected_matches >= 1 else "partial"
        return ClassificationDecision(label, (), rubric.source_refs if label == "understood" else (), False)
    return AnswerClassificationTool(create_provider(settings)).classify_with_rubric(rubric=rubric, answer=explanation)
