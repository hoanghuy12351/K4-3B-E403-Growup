"""Deterministic teaching-context extraction."""

import re

STOP_WORDS = {
    "about", "after", "also", "and", "are", "based", "before", "being", "between", "can", "concept", "context", "does", "for", "from", "into", "lesson", "more", "must", "not", "that", "the", "this", "through", "using", "with", "what", "which", "your",
    "các", "cho", "của", "được", "khái", "là", "một", "này", "những", "trong", "và", "về",
}


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _title_case(value: str) -> str:
    return value[:1].upper() + value[1:]


def extract_concepts(source_text: object = "", title: object = "", source_id: object = "") -> dict[str, object]:
    """Derive a small deterministic teaching context that a later service may replace."""
    text = _clean(source_text)
    heading = _clean(title)
    if not text and not heading:
        raise ValueError("Concept extraction requires sourceText or title.")
    candidates = [heading] if heading else []
    frequency: dict[str, int] = {}
    for word in re.findall(r"[^\W_][\w-]{2,}", f"{heading} {text}".lower(), flags=re.UNICODE):
        if word not in STOP_WORDS:
            frequency[word] = frequency.get(word, 0) + 1
    for word, _ in sorted(frequency.items(), key=lambda pair: (-pair[1], pair[0])):
        if not any(item.lower() == word for item in candidates):
            candidates.append(_title_case(word))
        if len(candidates) >= 3:
            break
    concepts = candidates[:3]
    primary_concept = concepts[0] if concepts else "Teaching concept"
    return {
        "topic": heading or primary_concept,
        "concepts": concepts,
        "learningObjectives": [f"Explain {primary_concept} using the supplied teaching material."],
        "sourceId": _clean(source_id) or None,
    }
