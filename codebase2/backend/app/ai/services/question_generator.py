"""Deterministic, source-grounded Phase 1 question generation."""

import re


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _first_relevant_sentence(text: str, concept: str) -> str:
    sentences = re.findall(r"[^.!?]+[.!?]?", _clean(text))
    return _clean(next((sentence for sentence in sentences if concept.lower() in sentence.lower()), sentences[0] if sentences else "The supplied teaching material defines this concept."))


def _question_id(value: str) -> str:
    slug = re.sub(r"[^\w]+", "-", _clean(value), flags=re.UNICODE).strip("-").upper()
    return f"Q-{slug or '001'}"


def generate_diagnostic_question(concept_context: dict[str, object] | None = None, misconceptions: list[dict[str, object]] | None = None, source_context: dict[str, object] | None = None) -> dict[str, object]:
    """Create one reviewable question using only the supplied teaching material."""
    concept_context = concept_context or {}
    source_context = source_context or {}
    concepts = concept_context.get("concepts") or []
    concept = _clean(concepts[0] if concepts else concept_context.get("topic"))
    source_text = _clean(source_context.get("text") or source_context.get("sourceText"))
    if not concept or not source_text:
        raise ValueError("Question generation requires a concept and supplied teaching material.")
    relevant = [item for item in misconceptions or [] if _clean(item.get("concept")).lower() == concept.lower()]
    options: list[dict[str, object]] = [{"id": "A", "text": _first_relevant_sentence(source_text, concept), "correct": True, "misconceptionId": None}]
    for item in relevant[:3]:
        options.append({"id": chr(65 + len(options)), "text": item["statement"], "correct": False, "misconceptionId": item["id"]})
    if len(options) == 1:
        options.append({"id": "B", "text": f"{concept} is unrelated to the supplied teaching material.", "correct": False, "misconceptionId": None})
    source_id = _clean(source_context.get("sourceId") or concept_context.get("sourceId"))
    objectives = concept_context.get("learningObjectives") or []
    return {
        "id": _question_id(source_id or concept),
        "topic": _clean(concept_context.get("topic")) or concept,
        "concept": concept,
        "question": f"Which statement about {concept} is supported by the supplied teaching material?",
        "learningObjective": _clean(objectives[0] if objectives else "") or f"Explain {concept} using the supplied teaching material.",
        "source": [{"type": "slide", "id": source_id or "teacher-supplied-context"}],
        "options": options,
    }
