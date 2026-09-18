"""Mocked NVIDIA OpenAI-compatible adapter tests."""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.config import AISettings
from app.ai.llm.errors import LLMConfigurationError, LLMMalformedResponseError
from app.ai.llm.providers.nvidia_provider import NvidiaProvider


class NvidiaProviderTests(unittest.TestCase):
    def settings(self):
        return AISettings(mode="llm", provider="nvidia", nvidia_api_key="test", nvidia_model="nim-model", nvidia_base_url="https://nim.example/v1", nvidia_api_style="chat_completions", max_retries=0)

    def test_uses_configured_chat_completion_and_parses_fenced_json(self):
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(id="chat-1", choices=[SimpleNamespace(message=SimpleNamespace(content=f"```json\n{json.dumps({'ok': True})}\n```"))], usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5))
        result = NvidiaProvider(self.settings(), client=client).generate_structured(system_prompt="system", user_prompt="user", schema={}, request_id="request-1")
        self.assertEqual(result.data, {"ok": True})
        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["model"], "nim-model")
        self.assertFalse(call["stream"])

    def test_missing_configuration_and_empty_content_fail(self):
        with self.assertRaises(LLMConfigurationError):
            NvidiaProvider(AISettings(mode="llm", provider="nvidia", nvidia_model="model"))
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[])
        with self.assertRaises(LLMMalformedResponseError):
            NvidiaProvider(self.settings(), client=client).generate_structured(system_prompt="s", user_prompt="u", schema={}, request_id="r")
