"""Semantic and grounding validation beyond provider structured output."""

import re

from pydantic import ValidationError

from .errors import LLMValidationError
from .models import LLMDiagnosticResult


def _terms(value: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[^\W_]{3,}", value, flags=re.UNICODE)}


def parse_and_validate(data: dict, *, evidence_turn_ids: set[str], teaching_context: dict) -> LLMDiagnosticResult:
    """Parse Pydantic output and reject invented citations or broken diagnostic semantics."""
    try:
        result = LLMDiagnosticResult.model_validate(data)
    except ValidationError as error:
        raise LLMValidationError("LLM output does not match the diagnostic contract.") from error
    misconception_ids = [item.id for item in result.misconceptions]
    if len(misconception_ids) != len(set(misconception_ids)):
        raise LLMValidationError("LLM output contains duplicate misconception IDs.")
    for misconception in result.misconceptions:
        if any(turn_id not in evidence_turn_ids for turn_id in misconception.evidenceTurnIds):
            raise LLMValidationError("LLM output references an evidence turn ID that was not supplied.")
    allowed_source_refs = {
        (str(item.get("type", "")).strip(), str(item.get("id", "")).strip())
        for item in teaching_context.get("allowedSourceRefs", [])
        if isinstance(item, dict)
    }
    allowed_source_ids = {source_id for _, source_id in allowed_source_refs} or {str(teaching_context.get("sourceId", "")).strip()}
    if not allowed_source_ids or "" in allowed_source_ids:
        raise LLMValidationError("Teaching context must provide sourceId for LLM grounding.")
    if any(source.id not in allowed_source_ids for source in result.question.source):
        raise LLMValidationError("LLM output references a source ID that was not supplied.")
    if allowed_source_refs and any((source.type, source.id) not in allowed_source_refs for source in result.question.source):
        raise LLMValidationError("LLM output references a source type that was not supplied.")
    options = result.question.options
    option_ids = [option.id for option in options]
    if len(option_ids) != len(set(option_ids)):
        raise LLMValidationError("LLM output contains duplicate option IDs.")
    correct_options = [option for option in options if option.correct]
    if len(correct_options) != 1:
        raise LLMValidationError("LLM output must contain exactly one correct option.")
    if correct_options[0].misconceptionId is not None:
        raise LLMValidationError("The correct option must have misconceptionId null.")
    known_misconceptions = set(misconception_ids)
    if any(option.misconceptionId and option.misconceptionId not in known_misconceptions for option in options):
        raise LLMValidationError("A diagnostic option references an unknown misconception ID.")
    teaching_terms = _terms(f"{teaching_context.get('title', '')} {teaching_context.get('text', '')}")
    answer_terms = _terms(correct_options[0].text)
    if teaching_terms and answer_terms and not teaching_terms.intersection(answer_terms):
        raise LLMValidationError("The correct option is not grounded in the supplied teaching material.")
    return result
