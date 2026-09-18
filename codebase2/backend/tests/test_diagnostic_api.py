"""HTTP tests for the AI diagnostic FastAPI vertical slice."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import AISettings
from app.ai.llm.errors import LLMProviderError, LLMTimeoutError
from app.main import app


VALID_PAYLOAD = {
    "teachingContext": {
        "title": "Tokenization",
        "text": "A token can be a word, part of a word, or a character.",
        "sourceId": "slide-test",
    },
    "options": {"questionCount": 1},
}

PIPELINE_RESULT = {
    "context": {"topic": "Tokenization", "concepts": ["token"]},
    "historicalEvidence": {"matchedQuestions": 1},
    "misconceptions": [],
    "questions": [{"id": "diagnostic-1"}],
    "generation": {"mode": "deterministic", "fallbackUsed": False},
}


class DiagnosticApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.settings_patch = patch("app.routers.diagnostic.AISettings.from_env", return_value=AISettings(mode="deterministic"))
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def test_health_returns_expected_payload(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "growup-backend"})

    @patch("app.routers.diagnostic.generate_diagnostic_check", return_value=PIPELINE_RESULT)
    def test_valid_request_calls_pipeline_once_and_preserves_result(self, pipeline_mock) -> None:
        response = self.client.post("/api/ai/diagnostic", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), PIPELINE_RESULT)
        pipeline_mock.assert_called_once()
        self.assertEqual(pipeline_mock.call_args.kwargs["teaching_context"], VALID_PAYLOAD["teachingContext"])
        self.assertEqual(pipeline_mock.call_args.kwargs["options"], VALID_PAYLOAD["options"])

    def test_missing_title_returns_422(self) -> None:
        payload = {"teachingContext": {"text": "Material"}}

        self.assertEqual(self.client.post("/api/ai/diagnostic", json=payload).status_code, 422)

    def test_whitespace_only_text_returns_422(self) -> None:
        payload = {"teachingContext": {"title": "Topic", "text": "   "}}

        self.assertEqual(self.client.post("/api/ai/diagnostic", json=payload).status_code, 422)

    def test_unknown_mode_and_provider_return_422(self) -> None:
        payload = {**VALID_PAYLOAD, "options": {"questionCount": 1, "mode": "invalid", "provider": "invalid"}}

        self.assertEqual(self.client.post("/api/ai/diagnostic", json=payload).status_code, 422)

    def test_question_count_above_one_returns_422(self) -> None:
        payload = {**VALID_PAYLOAD, "options": {"questionCount": 2}}

        self.assertEqual(self.client.post("/api/ai/diagnostic", json=payload).status_code, 422)

    @patch("app.routers.diagnostic.generate_diagnostic_check", side_effect=FileNotFoundError("dataset missing"))
    def test_missing_dataset_returns_503(self, _pipeline_mock) -> None:
        response = self.client.post("/api/ai/diagnostic", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "AI_DATA_UNAVAILABLE")

    @patch("app.routers.diagnostic.generate_diagnostic_check", side_effect=LLMProviderError("safe provider error"))
    def test_provider_error_returns_502(self, _pipeline_mock) -> None:
        response = self.client.post("/api/ai/diagnostic", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "AI_PROVIDER_ERROR")

    @patch("app.routers.diagnostic.generate_diagnostic_check", side_effect=LLMTimeoutError("safe timeout"))
    def test_provider_timeout_returns_504(self, _pipeline_mock) -> None:
        self.assertEqual(self.client.post("/api/ai/diagnostic", json=VALID_PAYLOAD).status_code, 504)

    @patch("app.routers.diagnostic.generate_diagnostic_check", side_effect=RuntimeError("secret-value"))
    def test_unexpected_error_is_sanitized(self, _pipeline_mock) -> None:
        response = self.client.post("/api/ai/diagnostic", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("secret-value", response.text)

    def test_local_cors_preflight_is_accepted(self) -> None:
        response = self.client.options(
            "/api/ai/diagnostic",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
