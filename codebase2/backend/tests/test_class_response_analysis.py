"""Tests for aggregate-only AI classroom analysis."""

from app.ai.config import AISettings
from app.ai.llm.models import ProviderResult
from app.ai.services.class_response_analysis import analyze_aggregate_responses


class _Provider:
    def __init__(self) -> None:
        self.user_prompt = ""

    def generate_structured(self, **kwargs) -> ProviderResult:
        self.user_prompt = kwargs["user_prompt"]
        return ProviderResult(
            data={
                "overview": "Phần lớn lớp chưa nắm vững khái niệm.",
                "pattern": "Nhiều học viên chọn phương án B.",
                "suggestedAction": "Dùng một phản ví dụ ngắn rồi hỏi lại.",
            },
            provider="test",
            model="test-model",
            latency_ms=1,
        )


def test_ai_receives_only_aggregate_multiple_choice_evidence(monkeypatch) -> None:
    provider = _Provider()
    monkeypatch.setattr("app.ai.services.class_response_analysis.create_provider", lambda settings: provider)
    result = analyze_aggregate_responses(
        question={"id": "q1", "question": "Câu hỏi?"},
        section_result={
            "concept": "Khái niệm", "recommendation": "reteach", "totalResponses": 10,
            "correctRate": 0.3, "dominantMisconception": {"statement": "Hiểu lầm X"},
            "optionDistribution": [{"optionId": "B", "count": 7, "ratio": 0.7, "correct": False}],
        },
        settings=AISettings(mode="llm", provider="openai"),
    )
    assert result["generatedBy"] == "ai"
    assert "participant" not in provider.user_prompt
    assert "displayName" not in provider.user_prompt


def test_insufficient_evidence_does_not_call_ai(monkeypatch) -> None:
    monkeypatch.setattr("app.ai.services.class_response_analysis.create_provider", lambda settings: (_ for _ in ()).throw(AssertionError("provider must not be called")))
    result = analyze_aggregate_responses(
        question={"id": "q1", "question": "Câu hỏi?"},
        section_result={
            "concept": "Khái niệm", "recommendation": "insufficient_data", "totalResponses": 1,
            "correctRate": 1.0, "dominantMisconception": None, "optionDistribution": [],
        },
        settings=AISettings(mode="llm", provider="openai"),
    )
    assert result["generatedBy"] == "rules"
