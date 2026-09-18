"""Evidence-backed deterministic grouping of historical question patterns."""

import re


def _normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _slug(value: object) -> str:
    result = re.sub(r"[^\w]+", "-", _normalize(value).lower(), flags=re.UNICODE).strip("-")
    return result or "concept"


def _excerpt(value: object, maximum: int = 220) -> str:
    text = _normalize(value)
    return f"{text[:maximum - 1]}…" if len(text) > maximum else text


def _classify_question(text: object) -> str:
    value = _normalize(text).lower()
    if re.search(r"difference|different|distinguish|versus|\bvs\b|khác|phân biệt", value):
        return "distinction"
    if re.search(r"what is|meaning|define|là gì|nghĩa là|định nghĩa", value):
        return "definition"
    if re.search(r"how|use|apply|cách|dùng|áp dụng", value):
        return "application"
    return "general"


def _statement(category: str, concept: str) -> str:
    statements = {
        "distinction": f"Possible historical confusion: {concept} may be conflated with a related concept.",
        "definition": f"Possible historical confusion: the definition or scope of {concept} may be unclear.",
        "application": f"Possible historical confusion: when or how to apply {concept} may be unclear.",
        "general": f"Possible historical question pattern: students requested clarification about {concept}.",
    }
    return statements[category]


def mine_misconceptions(concepts: list[str] | None = None, historical_questions: list[dict[str, object]] | None = None) -> dict[str, list[dict[str, object]]]:
    """Group question patterns and retain deduplicated short evidence by turn ID."""
    groups: dict[str, dict[str, object]] = {}
    for concept in [_normalize(value) for value in concepts or [] if _normalize(value)]:
        concept_terms = re.findall(r"[^\W_]{2,}", concept.lower(), flags=re.UNICODE)
        for question in historical_questions or []:
            text = _normalize(question.get("studentQuestion"))
            if not any(term in text.lower() for term in concept_terms):
                continue
            category = _classify_question(text)
            key = f"{_slug(concept)}-{category}"
            group = groups.setdefault(key, {"concept": concept, "category": category, "evidence": []})
            evidence = group["evidence"]
            assert isinstance(evidence, list)
            turn_id = str(question.get("turnId", ""))
            if len(evidence) < 5 and not any(item["turnId"] == turn_id for item in evidence):
                evidence.append({"turnId": turn_id, "excerpt": _excerpt(text)})
    misconceptions = []
    for index, (key, group) in enumerate(groups.items(), start=1):
        evidence = group["evidence"]
        assert isinstance(evidence, list)
        misconceptions.append({
            "id": f"M{index:03d}-{key}",
            "concept": group["concept"],
            "statement": _statement(str(group["category"]), str(group["concept"])),
            "evidence": evidence,
            "evidenceCount": len(evidence),
            "confidence": round(min(0.8, 0.35 + len(evidence) * 0.1), 2),
        })
    return {"misconceptions": misconceptions}
