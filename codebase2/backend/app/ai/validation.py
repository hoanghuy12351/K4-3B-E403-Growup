"""Dependency-free runtime validation for the diagnostic question contract."""


def validate_diagnostic_question(question: dict[str, object] | None) -> dict[str, object]:
    """Return clear validation errors without adding a JSON Schema dependency."""
    required = ("id", "topic", "concept", "question", "learningObjective", "source", "options")
    question = question or {}
    missing = [key for key in required if not question.get(key)]
    if missing:
        return {"valid": False, "errors": [f"Missing required fields: {', '.join(missing)}"]}
    options = question["options"]
    if not isinstance(options, list):
        return {"valid": False, "errors": ["Options must be a non-empty list."]}
    for option in options:
        if not isinstance(option, dict) or not option.get("id") or not option.get("text") or not isinstance(option.get("correct"), bool) or "misconceptionId" not in option:
            return {"valid": False, "errors": ["Every option must have id, text, correct, and misconceptionId."]}
    correct = [option for option in options if option["correct"] is True]
    if len(correct) != 1:
        return {"valid": False, "errors": ["Exactly one option must be marked correct."]}
    if correct[0]["misconceptionId"] is not None:
        return {"valid": False, "errors": ["A correct option must have misconceptionId: null."]}
    return {"valid": True, "errors": []}
