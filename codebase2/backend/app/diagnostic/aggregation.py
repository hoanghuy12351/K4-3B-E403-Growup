"""Evidence-first aggregation for lecturer diagnostic summaries."""

from typing import Any

from app.ai.config import response_coverage_settings
from app.ai.services.response_analyzer import analyze_responses

from .models import DiagnosticSession


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
        reason = "Chưa đủ phản hồi để đánh giá mức độ hiểu bài cho phần này."
    elif analysis["status"] == "understood":
        status = "understood"
        recommendation = "continue"
        reason = "Tỷ lệ trả lời đúng đạt ngưỡng hiểu bài."
    elif analysis["status"] == "uncertain":
        status = "uncertain"
        recommendation = "clarify"
        reason = "Kết quả cho thấy lớp cần được làm rõ thêm trước khi tiếp tục."
    else:
        status = "needs_attention"
        recommendation = "reteach"
        reason = "Kết quả cho thấy khái niệm này cần được giảng lại có trọng tâm."
    return {
        "sectionId": section["id"],
        "sectionTitle": section["title"],
        "concept": (section_data.get("concepts") or [question.get("concept")])[0],
        "totalResponses": response_count,
        "correctResponses": analysis["correctResponses"],
        "incorrectResponses": analysis["incorrectResponses"],
        "responseCoverage": coverage,
        "correctRate": analysis["correctRate"],
        "optionDistribution": [
            {
                "optionId": str(option["id"]),
                "text": str(option.get("text", "")),
                "count": sum(1 for item in response_objects if item.option_id == option["id"]),
                "ratio": round(sum(1 for item in response_objects if item.option_id == option["id"]) / response_count, 3) if response_count else 0,
                "correct": bool(option.get("correct")),
                "misconception": misconception_by_id.get(option.get("misconceptionId"), {}).get("statement"),
            }
            for option in question["options"]
        ],
        "misconceptionSignals": signals,
        "dominantMisconception": dominant_signal,
        "status": status,
        "recommendation": recommendation,
        "reason": reason,
        "scoringMethod": "answer_key",
        "aiAnalysis": session.analyses.get(str(question["id"])),
        "sourceRefs": section.get("sourceRefs", []),
    }


def build_class_summary(session: DiagnosticSession) -> dict[str, Any]:
    """Combine independent section evidence into a lecturer-facing suggestion."""
    section_results = [_section_result(session, section_data) for section_data in session.sections]
    student_count = len({response.participant_id for response in session.responses})
    joined_student_count = len(session.participants)
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
        reason = f"{target['concept']} chỉ có {target['correctRate']:.0%} phản hồi đúng. Nên giảng lại ngắn trước khi tiếp tục."
        evidence = {"sectionId": target["sectionId"], "responseCount": target["totalResponses"], "correctRate": target["correctRate"], "dominantMisconception": target["dominantMisconception"]}
    elif uncertain:
        recommendation = "clarify"
        overall_status = "uncertain"
        target = uncertain[0]
        reason = f"{target['concept']} có {target['correctRate']:.0%} phản hồi đúng. Nên làm rõ thêm trước khi tiếp tục."
        evidence = {"sectionId": target["sectionId"], "responseCount": target["totalResponses"], "correctRate": target["correctRate"], "dominantMisconception": target["dominantMisconception"]}
    elif understood and not insufficient:
        recommendation = "continue"
        overall_status = "understood"
        reason = "Các phần đều đạt ngưỡng hiểu bài và có đủ phản hồi."
        evidence = {"sectionCount": len(section_results), "responseCoverage": response_coverage}
    else:
        recommendation = "insufficient_data"
        overall_status = "insufficient_data"
        reason = "Chưa đủ phản hồi để đánh giá đáng tin cậy mức độ hiểu bài của lớp."
        evidence = {"sectionIds": [item["sectionId"] for item in insufficient], "minimumResponseCount": minimum_count, "minimumResponseCoverage": minimum_coverage}
    return {
        "sessionId": session.id,
        "responseCoverage": response_coverage,
        "respondingStudents": student_count,
        "joinedStudents": joined_student_count,
        "totalResponses": len(session.responses),
        "expectedStudents": session.expected_students,
        "sectionResults": section_results,
        "weakConcepts": weak_concepts,
        "overallStatus": overall_status,
        "recommendation": recommendation,
        "reason": reason,
        "evidence": evidence,
        "lecturerDecisionRequired": True,
    }
