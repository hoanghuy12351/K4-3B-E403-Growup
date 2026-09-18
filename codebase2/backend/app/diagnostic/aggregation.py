"""Evidence-first aggregation for lecturer diagnostic summaries."""

from typing import Any

from app.ai.config import response_coverage_settings
from app.ai.services.response_analyzer import analyze_responses

from .models import CheckpointRun, DiagnosticSession


def build_checkpoint_metrics(
    session: DiagnosticSession,
    run: CheckpointRun,
) -> tuple[dict[str, Any], str]:
    """Create an immutable, non-identifying snapshot for one closed run."""

    section_data = next(
        item for item in session.sections if item["question"]["id"] == run.question_id
    )
    question = section_data["question"]
    responses = [
        item for item in session.responses if item.checkpoint_run_id == run.id
    ]
    total = len(responses)
    correct = sum(item.correct for item in responses)
    correct_rate = round(correct / total, 3) if total else 0.0
    coverage = round(total / session.expected_students, 3) if session.expected_students else None

    option_distribution = []
    for option in question.get("options", []):
        count = sum(item.option_id == option.get("id") for item in responses)
        option_distribution.append({
            "optionId": option.get("id"),
            "text": option.get("text"),
            "count": count,
            "ratio": round(count / total, 3) if total else 0.0,
            "correct": bool(option.get("correct")),
            "misconceptionId": option.get("misconceptionId"),
        })

    misconception_by_id = {
        item.get("id"): item for item in section_data.get("misconceptions", [])
    }
    misconception_distribution = []
    for misconception_id in {
        item.misconception_id for item in responses if item.misconception_id
    }:
        count = sum(item.misconception_id == misconception_id for item in responses)
        misconception_distribution.append({
            "misconceptionId": misconception_id,
            "statement": misconception_by_id.get(misconception_id, {}).get("statement"),
            "count": count,
            "ratio": round(count / total, 3) if total else 0.0,
        })
    misconception_distribution.sort(key=lambda item: item["count"], reverse=True)

    minimum_count, minimum_coverage = response_coverage_settings()
    insufficient = total < minimum_count or (
        coverage is not None and coverage < minimum_coverage
    )
    if insufficient:
        computed_status = "insufficient_data"
    elif correct_rate >= 0.8:
        computed_status = "understood"
    elif correct_rate >= 0.6:
        computed_status = "mixed"
    else:
        computed_status = "needs_attention"

    metrics = {
        "sessionId": session.id,
        "checkpointRunId": run.id,
        "questionId": question["id"],
        "concept": question.get("concept"),
        "question": question.get("question"),
        "sourceRefs": question.get("source", []),
        "expectedStudents": session.expected_students,
        "respondingStudents": total,
        "responseCoverage": coverage,
        "correctResponses": correct,
        "incorrectResponses": total - correct,
        "correctRate": correct_rate,
        "optionDistribution": option_distribution,
        "misconceptionDistribution": misconception_distribution,
        "minimumResponseCount": minimum_count,
        "minimumResponseCoverage": minimum_coverage,
        "responseVersion": run.response_version,
    }
    return metrics, computed_status


def _section_result(session: DiagnosticSession, section_data: dict[str, Any]) -> dict[str, Any]:
    """Aggregate one section without exposing raw student identities or answers."""
    question = section_data["question"]
    section = section_data["section"]
    response_objects = [item for item in session.responses if item.question_id == question["id"]]
    responses = [item.to_dict() for item in response_objects]
    analysis = analyze_responses(question=question, responses=responses)
    response_count = analysis["totalResponses"]
    coverage = round(response_count / session.expected_students, 3) if session.expected_students else None
    minimum_count, minimum_coverage = response_coverage_settings()
    insufficient = response_count < minimum_count or (coverage is not None and coverage < minimum_coverage)
    misconception_by_id = {item.get("id"): item for item in section_data.get("misconceptions", [])}
    signals = []
    for signal in analysis["misconceptionSignals"]:
        misconception = misconception_by_id.get(signal["misconceptionId"], {})
        signals.append({**signal, "statement": misconception.get("statement")})
    dominant_signal = max(signals, key=lambda item: item["count"], default=None)
    if insufficient:
        status = "insufficient_data"
        recommendation = "insufficient_data"
        reason = "Not enough responses to infer class understanding for this section."
    elif analysis["status"] == "understood":
        status = "understood"
        recommendation = "continue"
        reason = "Response evidence meets the prototype understanding threshold."
    elif analysis["status"] == "uncertain":
        status = "uncertain"
        recommendation = "clarify"
        reason = "Response evidence suggests a short clarification may help before continuing."
    else:
        status = "needs_attention"
        recommendation = "reteach"
        reason = "Response evidence suggests this concept needs focused reteaching."
    return {
        "sectionId": section["id"],
        "sectionTitle": section["title"],
        "concept": (section_data.get("concepts") or [question.get("concept")])[0],
        "totalResponses": response_count,
        "correctResponses": analysis["correctResponses"],
        "incorrectResponses": analysis["incorrectResponses"],
        "responseCoverage": coverage,
        "correctRate": analysis["correctRate"],
        "misconceptionSignals": signals,
        "dominantMisconception": dominant_signal,
        "status": status,
        "recommendation": recommendation,
        "reason": reason,
        "signalDistribution": {
            signal: sum(1 for item in response_objects if item.signal == signal)
            for signal in ("correct_choice", "known_misconception", "incorrect_choice")
        },
        "sourceRefs": section.get("sourceRefs", []),
    }


def build_class_summary(session: DiagnosticSession) -> dict[str, Any]:
    """Combine independent section evidence into a lecturer-facing suggestion."""
    section_results = [_section_result(session, section_data) for section_data in session.sections]
    student_count = len({response.participant_id for response in session.responses})
    response_coverage = round(student_count / session.expected_students, 3) if session.expected_students else None
    needs_attention = [item for item in section_results if item["status"] == "needs_attention"]
    uncertain = [item for item in section_results if item["status"] == "uncertain"]
    understood = [item for item in section_results if item["status"] == "understood"]
    insufficient = [item for item in section_results if item["status"] == "insufficient_data"]
    weak_concepts = [
        {
            "sectionId": item["sectionId"],
            "concept": item["concept"],
            "status": item["status"],
            "correctRate": item["correctRate"],
            "dominantMisconception": item["dominantMisconception"],
        }
        for item in [*needs_attention, *uncertain]
    ]
    minimum_count, minimum_coverage = response_coverage_settings()
    if needs_attention:
        recommendation = "reteach"
        overall_status = "needs_attention"
        target = needs_attention[0]
        reason = f"{target['concept']} has a {target['correctRate']:.0%} correct rate. Suggested action: briefly reteach it before continuing."
        evidence = {"sectionId": target["sectionId"], "responseCount": target["totalResponses"], "correctRate": target["correctRate"], "dominantMisconception": target["dominantMisconception"]}
    elif uncertain:
        recommendation = "clarify"
        overall_status = "uncertain"
        target = uncertain[0]
        reason = f"{target['concept']} has a {target['correctRate']:.0%} correct rate. Suggested action: clarify it briefly before continuing."
        evidence = {"sectionId": target["sectionId"], "responseCount": target["totalResponses"], "correctRate": target["correctRate"], "dominantMisconception": target["dominantMisconception"]}
    elif understood and not insufficient:
        recommendation = "continue"
        overall_status = "understood"
        reason = "All sections meet the prototype understanding threshold with sufficient response evidence."
        evidence = {"sectionCount": len(section_results), "responseCoverage": response_coverage}
    else:
        recommendation = "insufficient_data"
        overall_status = "insufficient_data"
        reason = "Not enough section responses are available to infer class understanding reliably."
        evidence = {"sectionIds": [item["sectionId"] for item in insufficient], "minimumResponseCount": minimum_count, "minimumResponseCoverage": minimum_coverage}
    return {
        "sessionId": session.id,
        "responseCoverage": response_coverage,
        "respondingStudents": student_count,
        "expectedStudents": session.expected_students,
        "sectionResults": section_results,
        "weakConcepts": weak_concepts,
        "overallStatus": overall_status,
        "recommendation": recommendation,
        "reason": reason,
        "evidence": evidence,
        "lecturerDecisionRequired": True,
    }
