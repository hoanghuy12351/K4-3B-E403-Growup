"""High-level deterministic Phase 1 diagnostic pipeline."""

from typing import Any

from .config import AISettings, HISTORICAL_QUESTION_LIMIT, QUESTION_COUNT
from .data.vlearn_adapter import create_vlearn_adapter
from .llm.errors import LLMError
from .services.concept_extractor import extract_concepts
from .services.llm_diagnostic_service import generate_llm_diagnostic
from .services.misconception_miner import mine_misconceptions
from .services.question_generator import generate_diagnostic_question
from .validation import validate_diagnostic_question


def _deterministic_result(context: dict[str, Any], historical_questions: list[dict[str, Any]], teaching_context: dict[str, Any], options: dict[str, Any], generation: dict[str, Any]) -> dict[str, Any]:
    """Retain the exact Phase 1 behavior as the deterministic fallback implementation."""
    mined = mine_misconceptions(concepts=context["concepts"], historical_questions=historical_questions)
    question_count = max(1, min(int(options.get("questionCount") or QUESTION_COUNT), 1))
    questions = [
        generate_diagnostic_question(concept_context=context, misconceptions=mined["misconceptions"], source_context=teaching_context)
        for _ in range(question_count)
    ]
    for question in questions:
        validation = validate_diagnostic_question(question)
        if not validation["valid"]:
            raise ValueError(f"Generated diagnostic question is invalid: {' '.join(validation['errors'])}")
    return {"context": context, "historicalEvidence": {"matchedQuestions": len(historical_questions)}, "misconceptions": mined["misconceptions"], "questions": questions, "generation": generation}


def generate_diagnostic_check(teaching_context: dict[str, Any] | None = None, options: dict[str, Any] | None = None, adapter: Any = None, settings: AISettings | None = None) -> dict[str, Any]:
    """Prepare one diagnostic question using deterministic, LLM, or hybrid routing."""
    teaching_context = teaching_context or {}
    options = options or {}
    context = extract_concepts(
        source_text=teaching_context.get("text", ""),
        title=teaching_context.get("title", ""),
        source_id=teaching_context.get("sourceId", ""),
    )
    adapter = adapter or create_vlearn_adapter()
    historical_questions = adapter.get_question_examples_for_concept(
        concepts=context["concepts"],
        limit=options.get("historicalQuestionLimit") or HISTORICAL_QUESTION_LIMIT,
    )
    settings = settings or AISettings.from_env()
    deterministic_generation = {"mode": "deterministic", "provider": None, "model": None, "latencyMs": 0, "fallbackUsed": False, "fallbackReason": None, "retryCount": 0, "usage": None}
    if settings.mode == "deterministic":
        return _deterministic_result(context, historical_questions, teaching_context, options, deterministic_generation)
    try:
        llm_result, generation = generate_llm_diagnostic(teaching_context=teaching_context, concept_seed=context, historical_questions=historical_questions, settings=settings)
        return {
            "context": {"topic": llm_result.topic, "concepts": llm_result.concepts, "learningObjectives": [llm_result.learningObjective], "sourceId": teaching_context.get("sourceId") or None},
            "historicalEvidence": {"matchedQuestions": len(historical_questions)},
            "misconceptions": [{"id": item.id, "concept": item.concept, "statement": item.statement, "evidence": [{"turnId": turn_id, "excerpt": next((str(question.get('studentQuestion', ''))[: settings.max_evidence_chars] for question in historical_questions if question.get('turnId') == turn_id), "")} for turn_id in item.evidenceTurnIds], "evidenceCount": len(item.evidenceTurnIds), "confidence": round(min(0.8, 0.35 + len(item.evidenceTurnIds) * 0.1), 2)} for item in llm_result.misconceptions],
            "questions": [llm_result.question.model_dump()],
            "generation": generation,
        }
    except LLMError as error:
        if settings.mode == "hybrid" and settings.fallback_to_deterministic:
            fallback_generation = {**deterministic_generation, "fallbackUsed": True, "fallbackReason": str(error)}
            return _deterministic_result(context, historical_questions, teaching_context, options, fallback_generation)
        raise
