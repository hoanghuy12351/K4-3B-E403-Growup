"""OpenAI Responses API adapter with structured JSON output."""

import json
import time
from typing import Any

from ...config import AISettings
from ..client import retry_transient
from ..errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError
from ..models import ProviderResult

UNSUPPORTED_STRICT_SCHEMA_KEYWORDS = {
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
}


def _usage(response: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(response, "usage", None)
    return (getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None), getattr(usage, "total_tokens", None))


def _supports_temperature(model: str | None) -> bool:
    """Avoid unsupported sampling controls for the GPT-5 model family."""
    return not str(model or "").lower().startswith("gpt-5")


def _openai_strict_schema(value: Any) -> Any:
    """Remove JSON Schema constraints unsupported by OpenAI strict output mode."""
    if isinstance(value, list):
        return [_openai_strict_schema(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _openai_strict_schema(item)
            for key, item in value.items()
            if key not in UNSUPPORTED_STRICT_SCHEMA_KEYWORDS
        }
    return value


def _normalize_error(error: Exception) -> Exception:
    status = getattr(error, "status_code", None)
    if isinstance(error, TimeoutError):
        return LLMTimeoutError("OpenAI request timed out.")
    if status in {401, 403}:
        return LLMAuthenticationError("OpenAI authentication was rejected.")
    if status == 429:
        return LLMRateLimitError("OpenAI rate limit was reached.")
    if status == 400:
        return LLMConfigurationError("OpenAI rejected the request configuration.")
    if status in {408, 500, 502, 503, 504}:
        return LLMProviderError("OpenAI request failed temporarily.")
    return LLMProviderError("OpenAI request failed.")


class OpenAIProvider:
    """Use the official OpenAI Python SDK Responses API only."""

    def __init__(self, settings: AISettings, client: Any = None) -> None:
        if not settings.openai_api_key or not settings.openai_model:
            raise LLMConfigurationError("OpenAI requires OPENAI_API_KEY and OPENAI_MODEL.")
        self.settings = settings
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url, timeout=settings.timeout_seconds)
        self.client = client

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: dict, request_id: str) -> ProviderResult:
        """Make one Responses API request and safely parse its structured text."""
        def request() -> Any:
            try:
                request_options = {
                    "model": self.settings.openai_model,
                    "instructions": system_prompt,
                    "input": user_prompt,
                    "max_output_tokens": self.settings.max_output_tokens,
                    "store": False,
                    "text": {"format": {"type": "json_schema", "name": "classroom_diagnostic", "schema": _openai_strict_schema(schema), "strict": True}},
                }
                if _supports_temperature(self.settings.openai_model):
                    request_options["temperature"] = self.settings.temperature
                return self.client.responses.create(**request_options)
            except Exception as error:
                raise _normalize_error(error) from error

        started = time.perf_counter()
        response, retries = retry_transient(request, self.settings.max_retries)
        if getattr(response, "status", "completed") != "completed":
            raise LLMProviderError("OpenAI response did not complete.")
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise LLMMalformedResponseError("OpenAI response did not include structured output text.")
        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise LLMMalformedResponseError("OpenAI response contained invalid JSON.") from error
        input_tokens, output_tokens, total_tokens = _usage(response)
        return ProviderResult(data=data, provider="openai", model=self.settings.openai_model, latency_ms=round((time.perf_counter() - started) * 1000), request_id=getattr(response, "id", request_id), input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens, retry_count=retries)
