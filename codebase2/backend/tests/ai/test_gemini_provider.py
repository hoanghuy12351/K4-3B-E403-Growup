"""Mocked Gemini Interactions API adapter tests."""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.config import AISettings
from app.ai.llm.errors import LLMConfigurationError, LLMProviderError
from app.ai.llm.providers.gemini_provider import GeminiProvider


class GeminiProviderTests(unittest.TestCase):
    def settings(self):
        return AISettings(mode="llm", provider="gemini", gemini_api_key="test", gemini_model="configured-model", max_retries=0)

    def test_uses_interactions_response_format_and_output_text(self):
        client = MagicMock()
        client.interactions.create.return_value = SimpleNamespace(status="completed", id="interaction-1", output_text=json.dumps({"ok": True}), usage_metadata=None)
        result = GeminiProvider(self.settings(), client=client).generate_structured(system_prompt="system", user_prompt="user", schema={"type": "object"}, request_id="request-1")
        self.assertEqual(result.data, {"ok": True})
        call = client.interactions.create.call_args.kwargs
        self.assertEqual(call["model"], "configured-model")
        self.assertEqual(call["response_format"]["mime_type"], "application/json")

    def test_missing_key_and_incomplete_interaction_fail(self):
        with self.assertRaises(LLMConfigurationError):
            GeminiProvider(AISettings(mode="llm", provider="gemini", gemini_model="model"))
        client = MagicMock()
        client.interactions.create.return_value = SimpleNamespace(status="incomplete", output_text=None)
        with self.assertRaises(LLMProviderError):
            GeminiProvider(self.settings(), client=client).generate_structured(system_prompt="s", user_prompt="u", schema={}, request_id="r")
