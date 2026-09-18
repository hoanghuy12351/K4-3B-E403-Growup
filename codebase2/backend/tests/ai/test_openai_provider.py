"""Mocked OpenAI Responses API adapter tests."""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.config import AISettings
from app.ai.llm.errors import LLMAuthenticationError, LLMConfigurationError, LLMTimeoutError
from app.ai.llm.providers.openai_provider import OpenAIProvider


class ApiError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class OpenAIProviderTests(unittest.TestCase):
    def settings(self):
        return AISettings(mode="llm", provider="openai", openai_api_key="test", openai_model="configured-model", max_retries=0)

    def test_uses_responses_with_schema_and_parses_output(self):
        client = MagicMock()
        client.responses.create.return_value = SimpleNamespace(status="completed", id="resp-1", output_text=json.dumps({"ok": True}), usage=SimpleNamespace(input_tokens=2, output_tokens=3, total_tokens=5))
        result = OpenAIProvider(self.settings(), client=client).generate_structured(system_prompt="system", user_prompt="user", schema={"type": "object"}, request_id="request-1")
        self.assertEqual(result.data, {"ok": True})
        self.assertEqual(result.model, "configured-model")
        call = client.responses.create.call_args.kwargs
        self.assertEqual(call["model"], "configured-model")
        self.assertEqual(call["text"]["format"]["type"], "json_schema")

    def test_missing_key_is_clear_configuration_error(self):
        with self.assertRaises(LLMConfigurationError):
            OpenAIProvider(AISettings(mode="llm", provider="openai", openai_model="model"))

    def test_authentication_and_timeout_are_normalized(self):
        client = MagicMock()
        client.responses.create.side_effect = ApiError(401)
        with self.assertRaises(LLMAuthenticationError):
            OpenAIProvider(self.settings(), client=client).generate_structured(system_prompt="s", user_prompt="u", schema={}, request_id="r")
        client.responses.create.side_effect = TimeoutError()
        with self.assertRaises(LLMTimeoutError):
            OpenAIProvider(self.settings(), client=client).generate_structured(system_prompt="s", user_prompt="u", schema={}, request_id="r")
