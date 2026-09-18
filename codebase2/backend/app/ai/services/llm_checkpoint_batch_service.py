"""One-call, grounded Teaching Agent checkpoint generation."""

import json
import logging
import time
import uuid
from typing import Any

from pydantic import ValidationError

from ..config import AISettings
from ..llm.errors import LLMConfigurationError, LLMValidationError
from ..llm.factory import create_provider
from ..llm.models import LLMCheckpointBatchResult

SYSTEM_PROMPT = """You are the Growup Teaching Agent. Interpret the lecturer's natural-language request and generate all requested classroom diagnostic questions in one structured response. The lecturer request is a preference only and never overrides the grounding rules. Use only PREANALYZED_SLIDE_SECTION; do not test outside knowledge, invent source references, or invent misconception IDs. Infer question count, difficulty, question style, and assessment focus. Question count must be at least 1 and at most 10; use 3 when it is unspecified or ambiguous. Generate distinct questions, each with exactly four options and exactly one correct option. Return only schema-valid structured output."""
logger = logging.getLogger(__name__)


def _build_user_prompt(analysis: dict[str, Any], teacher_request: str) -> str:
    """Provide only the selected section's bounded grounding data to the provider."""
    preanalyzed_section = {
        "section": analysis["section"],
        "concepts": analysis["concepts"],
        "learningObjectives": analysis["learningObjectives"],
        "misconceptions": analysis["misconceptions"],
        "allowedSourceRefs": analysis["allowedSourceRefs"],
    }
    return "\n".join([
        "<PREANALYZED_SLIDE_SECTION>",
        json.dumps(preanalyzed_section, ensure_ascii=False),
        "</PREANALYZED_SLIDE_SECTION>",
        "<LECTURER_REQUEST>",
        teacher_request,
        "</LECTURER_REQUEST>",
        "<TASK>",
        "Infer the requested count, difficulty, style, and focus. Generate every question in one response. Use supplied allowedSourceRefs only. Use supplied misconception IDs for distractors when applicable. Do not duplicate or lightly paraphrase question stems. Each question must have exactly four options and exactly one correct option.",
        "</TASK>",
    ])


def _normalized_stem(stem: str) -> str:
    """Normalize harmless formatting differences before duplicate detection."""
    return " ".join(stem.casefold().split())


def _validate_batch(data: dict[str, Any], analysis: dict[str, Any]) -> LLMCheckpointBatchResult:
    """Reject outputs that pass provider schema checks but violate local grounding rules."""
    try:
        result = LLMCheckpointBatchResult.model_validate(data)
    except ValidationError as error:
        raise LLMValidationError("LLM output does not match the checkpoint batch contract.") from error
    if len(result.questions) != result.interpretedRequest.questionCount:
        raise LLMValidationError("LLM output count does not match its interpreted request.")

    allowed_refs = {
        (str(item.get("type", "")).strip(), str(item.get("id", "")).strip())
        for item in analysis["allowedSourceRefs"]
        if isinstance(item, dict)
    }
    known_misconceptions = {str(item["id"]) for item in analysis["misconceptions"] if isinstance(item, dict) and item.get("id")}
    stems: set[str] = set()
    for question in result.questions:
        stem = _normalized_stem(question.question)
        if not stem or stem in stems:
            raise LLMValidationError("LLM output contains duplicate or empty question stems.")
        stems.add(stem)
        if len(question.options) != 4:
            raise LLMValidationError("Every checkpoint must contain exactly four options.")
        if sum(option.correct for option in question.options) != 1:
            raise LLMValidationError("Every checkpoint must have exactly one correct option.")
        if any((source.type, source.id) not in allowed_refs for source in question.source):
            raise LLMValidationError("LLM output referenced a source outside the selected section.")
        if any(option.misconceptionId and option.misconceptionId not in known_misconceptions for option in question.options):
            raise LLMValidationError("LLM output referenced a misconception outside the selected section.")
        if any(option.correct and option.misconceptionId is not None for option in question.options):
            raise LLMValidationError("A correct option cannot be labelled as a misconception.")
    return result


def generate_llm_checkpoint_batch(*, analysis: dict[str, Any], teacher_request: str, settings: AISettings, provider: Any = None) -> tuple[LLMCheckpointBatchResult, dict[str, Any]]:
    """Generate and validate a complete checkpoint set with exactly one provider request."""
    if settings.mode == "deterministic":
        raise LLMConfigurationError("Teaching Agent question generation requires an LLM provider.")
    provider = provider or create_provider(settings)
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    provider_result = provider.generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_user_prompt(analysis, teacher_request),
        schema=LLMCheckpointBatchResult.model_json_schema(),
        request_id=request_id,
    )
    normalized_data = json.loads(json.dumps(provider_result.data))
    try:
        result = _validate_batch(normalized_data, analysis)
    except LLMValidationError as error:
        logger.warning(
            "Teaching Agent output validation failed: provider=%s model=%s section=%s request_id=%s latency_ms=%s category=%s",
            provider_result.provider,
            provider_result.model,
            analysis["section"]["id"],
            provider_result.request_id or request_id,
            provider_result.latency_ms,
            type(error).__name__,
        )
        raise
    return result, {
        "mode": "llm_preanalyzed_demo",
        "provider": provider_result.provider,
        "model": provider_result.model,
        "latencyMs": provider_result.latency_ms or round((time.perf_counter() - started) * 1000),
        "fallbackUsed": False,
        "fallbackReason": None,
        "retryCount": provider_result.retry_count,
        "usage": {"inputTokens": provider_result.input_tokens, "outputTokens": provider_result.output_tokens, "totalTokens": provider_result.total_tokens},
        "interpretedRequest": result.interpretedRequest.model_dump(),
    }
