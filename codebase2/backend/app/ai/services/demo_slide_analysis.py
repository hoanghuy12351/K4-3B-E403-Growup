"""Expose bounded, pre-analyzed evidence for the fixed Teaching Agent demo."""

from copy import deepcopy
import json
from typing import Any

from app.ai.config import AISettings
from app.ai.llm.errors import LLMError, LLMValidationError
from app.ai.services.llm_diagnostic_service import generate_llm_diagnostic

from .demo_checkpoint_catalog import (
    DemoCheckpointCatalogError,
    _section_source_refs,
    get_demo_checkpoint,
    get_demo_section,
    load_demo_catalog,
)


def get_preanalyzed_section(section_id: str) -> dict[str, Any]:
    """Return selected slide-analysis data without loading PDFs or transcripts at runtime."""
    section = get_demo_section(section_id)
    checkpoint = get_demo_checkpoint(section_id)
    lesson = load_demo_catalog().get("lesson")
    if not isinstance(lesson, dict):
        raise DemoCheckpointCatalogError("Preset demo lesson metadata is invalid.")
    question = checkpoint.get("question")
    if not isinstance(question, dict) or not isinstance(question.get("source"), list):
        raise DemoCheckpointCatalogError("Preset demo analysis has invalid source references.")
    allowed_refs = _section_source_refs(section, question["source"])
    concepts = checkpoint.get("concepts")
    objectives = checkpoint.get("learningObjectives")
    misconceptions = checkpoint.get("misconceptions")
    if not all(isinstance(value, list) for value in (concepts, objectives, misconceptions)):
        raise DemoCheckpointCatalogError("Preset demo analysis is incomplete.")
    return {
        "lesson": {"id": lesson["id"], "title": lesson["title"]},
        "section": {"id": section["id"], "title": section["title"], "order": section["order"], "slidePages": section["slidePages"]},
        "concepts": concepts,
        "learningObjectives": objectives,
        "misconceptions": misconceptions,
        "allowedSourceRefs": allowed_refs,
    }


def _fallback_question(analysis: dict[str, Any], index: int, reason: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Use a validated local fixture only when hybrid generation cannot complete."""
    checkpoint = get_demo_checkpoint(analysis["section"]["id"])
    question = deepcopy(checkpoint["question"])
    question["id"] = f"{analysis['section']['id']}-q{index:02d}"
    if index == 2:
        question["question"] = f"Trong một tình huống thực tế, lựa chọn nào áp dụng đúng nội dung {analysis['section']['title']}?"
    elif index == 3:
        question["question"] = f"Nhận định nào giúp kiểm tra đúng nhất mức hiểu về {analysis['section']['title']}?"
    return question, {
        "mode": "llm_preanalyzed_demo",
        "provider": None,
        "model": None,
        "latencyMs": 0,
        "fallbackUsed": True,
        "fallbackReason": reason,
        "retryCount": 0,
        "usage": None,
    }


def generate_preanalyzed_checkpoints(*, analysis: dict[str, Any], teacher_request: str, question_count: int, settings: AISettings) -> list[dict[str, Any]]:
    """Generate up to three grounded questions without touching raw lesson files."""
    preanalyzed = {
        "section": analysis["section"],
        "concepts": analysis["concepts"],
        "learningObjectives": analysis["learningObjectives"],
        "misconceptions": analysis["misconceptions"],
        "allowedSourceRefs": analysis["allowedSourceRefs"],
    }
    teaching_context = {
        "title": analysis["section"]["title"],
        "text": " ".join([*analysis["concepts"], *analysis["learningObjectives"], *[item["statement"] for item in analysis["misconceptions"]]]),
        "sourceId": analysis["lesson"]["id"],
        "allowedSourceRefs": analysis["allowedSourceRefs"],
        "preanalyzedSection": preanalyzed,
    }
    seed = {"concepts": analysis["concepts"], "learningObjectives": analysis["learningObjectives"]}
    known_misconceptions = {item["id"] for item in analysis["misconceptions"]}
    sections: list[dict[str, Any]] = []
    previous_questions: list[str] = []
    for index in range(1, question_count + 1):
        variation = "\n".join([
            f"Question {index}/{question_count}.",
            "Use a different assessment angle, correct-answer wording, and distractor set from every previous question.",
            "Do not repeat or lightly paraphrase a previous question stem.",
            "<PREVIOUS_QUESTIONS>",
            json.dumps(previous_questions, ensure_ascii=False),
            "</PREVIOUS_QUESTIONS>",
        ])
        try:
            if settings.mode == "deterministic":
                raise LLMValidationError("AI generation is disabled by AI_MODE.")
            result, generation = generate_llm_diagnostic(
                teaching_context=teaching_context,
                concept_seed=seed,
                historical_questions=[],
                settings=settings,
                teacher_request=teacher_request,
                variation_instruction=variation,
            )
            question = result.question.model_dump()
            if len(question["options"]) != 4:
                raise LLMValidationError("LLM output must contain exactly four options for the demo.")
            used_misconceptions = {option["misconceptionId"] for option in question["options"] if option["misconceptionId"]}
            if not used_misconceptions.issubset(known_misconceptions):
                raise LLMValidationError("LLM output referenced a misconception outside the selected section.")
            if not {item.id for item in result.misconceptions}.issubset(known_misconceptions):
                raise LLMValidationError("LLM output defined a misconception outside the selected section.")
            question["id"] = f"{analysis['section']['id']}-q{index:02d}"
            generation["mode"] = "llm_preanalyzed_demo"
        except LLMError as error:
            if settings.mode != "hybrid" or not settings.fallback_to_deterministic:
                raise
            question, generation = _fallback_question(analysis, index, str(error))
        section_id = f"{analysis['section']['id']}-q{index:02d}"
        previous_questions.append(str(question["question"]))
        sections.append({
            "sectionId": section_id,
            "section": {"id": section_id, "title": f"{analysis['section']['title']} — Câu {index}", "order": index, "sourceRefs": analysis["allowedSourceRefs"]},
            "concepts": analysis["concepts"],
            "learningObjectives": analysis["learningObjectives"],
            "misconceptions": analysis["misconceptions"],
            "historicalEvidence": {"matchedQuestions": 0},
            "question": question,
            "generation": generation,
        })
    return sections
