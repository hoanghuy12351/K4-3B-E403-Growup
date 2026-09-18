"""Tests for server-only .env loading without reading any real credential."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.config import AISettings


class AISettingsTests(unittest.TestCase):
    def test_loads_provider_values_from_an_explicit_env_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            env_file = Path(directory) / ".env"
            env_file.write_text("AI_MODE=llm\nAI_PROVIDER=openai\nOPENAI_API_KEY=local-test-key\nOPENAI_MODEL=test-model\n", encoding="utf-8")
            settings = AISettings.from_env(env_file)
        self.assertEqual(settings.mode, "llm")
        self.assertEqual(settings.openai_api_key, "local-test-key")
        self.assertEqual(settings.openai_model, "test-model")

    def test_exported_environment_value_has_priority_over_env_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "exported-key"}, clear=True):
            env_file = Path(directory) / ".env"
            env_file.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
            settings = AISettings.from_env(env_file)
        self.assertEqual(settings.openai_api_key, "exported-key")
