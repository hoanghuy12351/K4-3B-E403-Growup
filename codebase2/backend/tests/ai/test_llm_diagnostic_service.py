"""Mocked service and pipeline mode tests; no provider network calls occur."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import AISettings, generate_diagnostic_check
from app.ai.llm.errors import LLMMalformedResponseError, LLMProviderError, LLMValidationError
from app.ai.llm.models import LLMDiagnosticResult, ProviderResult
from app.ai.services.llm_diagnostic_service import generate_llm_diagnostic


class StubAdapter:
    def get_question_examples_for_concept(self, concepts, limit):
        return [{"turnId": "T00001", "studentQuestion": "What is the difference between a token and a word?"}]


class StubProvider:
    def __init__(self, data):
        self.data = data

    def generate_structured(self, **kwargs):
        return ProviderResult(data=self.data, provider="openai", model="mock-model", latency_ms=12)


def valid_payload():
    return {"topic": "Tokenization", "concepts": ["Tokenization"], "learningObjective": "Explain tokenization.", "misconceptions": [{"id": "M001", "concept": "Tokenization", "statement": "Possible historical confusion.", "evidenceTurnIds": ["T00001"]}], "question": {"id": "Q1", "topic": "Tokenization", "concept": "Tokenization", "question": "Which statement is supported?", "learningObjective": "Explain tokenization.", "source": [{"type": "slide", "id": "slide-12"}], "options": [{"id": "A", "text": "A token can be a word.", "correct": True, "misconceptionId": None}, {"id": "B", "text": "A possible confusion.", "correct": False, "misconceptionId": "M001"}]}}


class LLMDiagnosticServiceTests(unittest.TestCase):
    def context(self):
        return {"title": "Tokenization", "text": "A token can be a word, part of a word, or a character.", "sourceId": "slide-12"}

    def test_service_bounds_evidence_and_builds_safe_result(self):
        result, metadata = generate_llm_diagnostic(teaching_context=self.context(), concept_seed={"topic": "Tokenization", "concepts": ["Tokenization"]}, historical_questions=StubAdapter().get_question_examples_for_concept([], 1), settings=AISettings(mode="llm", provider="openai", openai_api_key="test", openai_model="mock", max_historical_questions=1), provider=StubProvider(valid_payload()))
        self.assertEqual(result.question.id, "Q1")
        self.assertFalse(metadata["fallbackUsed"])

    def test_deterministic_and_hybrid_fallback_modes(self):
        deterministic = generate_diagnostic_check(teaching_context=self.context(), adapter=StubAdapter(), settings=AISettings(mode="deterministic"))
        self.assertEqual(deterministic["generation"]["mode"], "deterministic")
        with patch("app.ai.pipeline.generate_llm_diagnostic", side_effect=LLMProviderError("provider unavailable")):
            hybrid = generate_diagnostic_check(teaching_context=self.context(), adapter=StubAdapter(), settings=AISettings(mode="hybrid", provider="openai", openai_api_key="test", openai_model="mock"))
        self.assertTrue(hybrid["generation"]["fallbackUsed"])

    def test_hybrid_falls_back_for_malformed_or_ungrounded_llm_output(self):
        settings = AISettings(mode="hybrid", provider="openai", openai_api_key="test", openai_model="mock")
        for error in (LLMMalformedResponseError("invalid JSON"), LLMValidationError("invented evidence ID"), LLMValidationError("invented source ID")):
            with self.subTest(error=type(error).__name__), patch("app.ai.pipeline.generate_llm_diagnostic", side_effect=error):
                result = generate_diagnostic_check(teaching_context=self.context(), adapter=StubAdapter(), settings=settings)
                self.assertTrue(result["generation"]["fallbackUsed"])

    def test_llm_mode_returns_mocked_llm_result_without_fallback(self):
        llm_result = LLMDiagnosticResult.model_validate(valid_payload())
        metadata = {"mode": "llm", "provider": "openai", "model": "mock-model", "latencyMs": 12, "fallbackUsed": False, "fallbackReason": None, "retryCount": 0, "usage": None}
        with patch("app.ai.pipeline.generate_llm_diagnostic", return_value=(llm_result, metadata)):
            result = generate_diagnostic_check(teaching_context=self.context(), adapter=StubAdapter(), settings=AISettings(mode="llm", provider="openai", openai_api_key="test", openai_model="mock"))
        self.assertEqual(result["generation"]["mode"], "llm")
        self.assertEqual(result["questions"][0]["id"], "Q1")
