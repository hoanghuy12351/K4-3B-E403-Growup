"""Make one tiny real provider request only when the user has configured credentials."""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import AISettings
from app.ai.llm.factory import create_provider
from app.ai.llm.models import LLMDiagnosticResult


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely smoke-test a configured LLM provider.")
    parser.add_argument("--provider", required=True, choices=["openai", "gemini", "nvidia"])
    args = parser.parse_args()
    settings = replace(AISettings.from_env(), mode="llm", provider=args.provider)
    try:
        result = create_provider(settings).generate_structured(
            system_prompt="Return only the requested JSON. Do not use tools.",
            user_prompt="Create a one-option-free diagnostic result for: A token can be a word. Source ID: smoke-slide.",
            schema=LLMDiagnosticResult.model_json_schema(),
            request_id="manual-smoke-test",
        )
        LLMDiagnosticResult.model_validate(result.data)
    except Exception as error:
        print(f"Provider: {args.provider}\nSuccess: false\nError: {type(error).__name__}")
        return 1
    print(f"Provider: {result.provider}\nModel: {result.model}\nSuccess: true\nLatency: {result.latency_ms} ms\nStructured parse valid: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
