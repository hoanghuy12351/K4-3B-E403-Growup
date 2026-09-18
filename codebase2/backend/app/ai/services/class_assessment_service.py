"""Orchestrate deterministic and LLM class-level checkpoint reporting."""

from typing import Any

from app.ai.config import AISettings
from app.ai.llm.errors import LLMError
from app.ai.llm.factory import create_provider
from app.domain.classification import ClassificationError
from app.tools.class_assessment import ClassAssessmentTool


def _deterministic_report(metrics: dict[str, Any], computed_status: str) -> dict[str, Any]:
    """Always-available report built from aggregate facts only."""

    correct_rate = float(metrics["correctRate"])
    misconception_distribution = metrics.get("misconceptionDistribution", [])
    top = max(misconception_distribution, key=lambda item: item["count"], default=None)
    if computed_status == "insufficient_data":
        summary = "Chưa đủ câu trả lời để đánh giá đáng tin cậy tình trạng của lớp."
        action = "collect_more"
        moves = ["Chờ thêm học viên trả lời trước khi quyết định tiếp tục bài học."]
    elif computed_status == "understood":
        summary = f"Lớp đạt tỷ lệ trả lời đúng {correct_rate:.0%}; bằng chứng hiện tại cho thấy đa số đã nắm được khái niệm."
        action = "continue"
        moves = ["Tiếp tục sang phần tiếp theo và nhắc ngắn lại đáp án đúng."]
    elif computed_status == "mixed":
        summary = f"Lớp đạt tỷ lệ trả lời đúng {correct_rate:.0%}; mức độ hiểu còn chưa đồng đều."
        action = "clarify"
        moves = ["Làm rõ điểm gây nhầm lẫn chính trước khi tiếp tục."]
    else:
        summary = f"Lớp chỉ đạt tỷ lệ trả lời đúng {correct_rate:.0%}; khái niệm cần được củng cố lại."
        action = "reteach"
        moves = ["Giảng lại ngắn gọn khái niệm và dùng một ví dụ đối chiếu."]

    key_misconceptions = []
    if top:
        key_misconceptions.append({
            "id": top["misconceptionId"],
            "count": top["count"],
            "ratio": top["ratio"],
            "statement": top.get("statement"),
            "severity": "high" if top["ratio"] >= 0.3 else "medium" if top["ratio"] >= 0.15 else "low",
            "interpretation": top.get("statement") or "Distractor này được nhiều học viên lựa chọn.",
        })
    return {
        "summary": summary,
        "keyMisconceptions": key_misconceptions,
        "recommendedAction": action,
        "teachingMoves": moves,
        "followUpQuestion": None,
        "confidence": 1.0 if computed_status != "insufficient_data" else 0.4,
        "limitations": [] if computed_status != "insufficient_data" else ["Số lượng hoặc độ phủ câu trả lời chưa đạt ngưỡng tối thiểu."],
        "teacherDecisionRequired": True,
        "generation": {"mode": "deterministic", "fallbackUsed": False},
    }


def generate_class_assessment(
    *, metrics: dict[str, Any], computed_status: str, settings: AISettings
) -> dict[str, Any]:
    """Generate one aggregate report, falling back safely in hybrid mode."""

    if settings.mode == "deterministic" or computed_status == "insufficient_data":
        return _deterministic_report(metrics, computed_status)
    try:
        report = ClassAssessmentTool(create_provider(settings)).generate_report(
            metrics=metrics, computed_status=computed_status
        )
        report["generation"] = {
            "mode": "llm", "provider": settings.provider, "fallbackUsed": False
        }
        return report
    except (LLMError, ClassificationError) as error:
        if settings.mode == "hybrid" and settings.fallback_to_deterministic:
            report = _deterministic_report(metrics, computed_status)
            report["generation"] = {
                "mode": "deterministic", "provider": settings.provider,
                "fallbackUsed": True, "fallbackReason": str(error),
            }
            return report
        raise
