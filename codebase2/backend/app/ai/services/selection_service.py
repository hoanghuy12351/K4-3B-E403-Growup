"""Deterministic classification for one multiple-choice selection.

There is deliberately no LLM call here: a selected option already carries its
correctness and optional misconception ID in the server-owned question.
"""

from dataclasses import dataclass

from app.domain.classification import ConceptRubric


@dataclass(frozen=True)
class SelectionResult:
    """Minimal internal signal later consumed by class-level aggregation."""

    correct: bool
    signal: str
    misconception_id: str | None


def classify_selection(*, rubric: ConceptRubric, selected_option_id: str) -> SelectionResult:
    """Map an option to an objective correctness/misconception signal."""

    option = rubric.option(selected_option_id)
    if option.correct:
        return SelectionResult(True, "correct_choice", None)
    if option.misconception_id in rubric.allowed_misconceptions:
        return SelectionResult(False, "known_misconception", option.misconception_id)
    return SelectionResult(False, "incorrect_choice", None)
