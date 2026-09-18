"""Deterministic response aggregation for lecturer decision support."""

from ..config import RESPONSE_THRESHOLDS


def analyze_responses(question: dict[str, object] | None = None, responses: list[dict[str, object]] | None = None, thresholds: dict[str, float] | None = None) -> dict[str, object]:
    """Aggregate recognized option selections with configurable prototype thresholds."""
    question = question or {}
    if not question.get("options"):
        raise ValueError("Response analysis requires a diagnostic question with options.")
    thresholds = thresholds or RESPONSE_THRESHOLDS
    options = {option["id"]: option for option in question["options"]}
    accepted = [response for response in responses or [] if response.get("optionId") in options]
    total_responses = len(accepted)
    correct_count = sum(bool(options[response["optionId"]]["correct"]) for response in accepted)
    correct_rate = round(correct_count / total_responses, 3) if total_responses else 0
    status = "understood" if correct_rate >= thresholds["understood"] else "uncertain" if correct_rate >= thresholds["uncertain"] else "needs_attention"
    signal_counts: dict[str, int] = {}
    for response in accepted:
        misconception_id = options[response["optionId"]].get("misconceptionId")
        if misconception_id:
            signal_counts[misconception_id] = signal_counts.get(misconception_id, 0) + 1
    signals = [{"misconceptionId": misconception_id, "count": count, "ratio": round(count / total_responses, 3)} for misconception_id, count in signal_counts.items()]
    recommendation = "Continue to the next concept block." if status == "understood" else "Ask for one brief clarification before continuing." if status == "uncertain" else f"Briefly clarify {question.get('concept', '')} before continuing."
    return {"totalResponses": total_responses, "correctRate": correct_rate, "status": status, "misconceptionSignals": signals, "recommendation": recommendation}
