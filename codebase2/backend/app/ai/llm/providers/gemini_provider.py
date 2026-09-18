"""Gemini Interactions API adapter with JSON response format."""

import json
import time
from typing import Any

from ...config import AISettings
from ..client import retry_transient
from ..errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError
from ..models import ProviderResult


def _normalize_error(error: Exception) -> Exception:
    status = getattr(error, "status_code", None)
    if isinstance(error, TimeoutError):
        return LLMTimeoutError("Gemini request timed out.")
    if status in {401, 403}:
        return LLMAuthenticationError("Gemini authentication was rejected.")
    if status == 429:
        return LLMRateLimitError("Gemini rate limit was reached.")
    if status == 400:
        return LLMConfigurationError("Gemini rejected the request configuration.")
    if status in {408, 500, 502, 503, 504}:
        return LLMProviderError("Gemini request failed temporarily.")
    return LLMProviderError("Gemini request failed.")


class GeminiProvider:
    """Use the current google-genai Interactions API, not generateContent."""

    def __init__(self, settings: AISettings, client: Any = None) -> None:
        if not settings.gemini_api_key or not settings.gemini_model:
            raise LLMConfigurationError("Gemini requires GEMINI_API_KEY and GEMINI_MODEL.")
        self.settings = settings
        if client is None:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
        self.client = client

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: dict, request_id: str) -> ProviderResult:
        """Make one Interactions API request and parse output_text as JSON."""
        def request() -> Any:
            try:
                return self.client.interactions.create(
                    model=self.settings.gemini_model,
                    system_instruction=system_prompt,
                    input=user_prompt,
                    store=False,
                    response_format={"type": "text", "mime_type": "application/json", "schema": schema},
                )
            except Exception as error:
                raise _normalize_error(error) from error

        started = time.perf_counter()
        interaction, retries = retry_transient(request, self.settings.max_retries)
        if getattr(interaction, "status", "completed") in {"failed", "cancelled", "incomplete"}:
            raise LLMProviderError("Gemini interaction did not complete.")
        output_text = getattr(interaction, "output_text", None)
        if not output_text:
            raise LLMMalformedResponseError("Gemini interaction did not include structured output text.")
        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise LLMMalformedResponseError("Gemini interaction contained invalid JSON.") from error
        usage = getattr(interaction, "usage_metadata", None)
        return ProviderResult(data=data, provider="gemini", model=self.settings.gemini_model, latency_ms=round((time.perf_counter() - started) * 1000), request_id=getattr(interaction, "id", request_id), input_tokens=getattr(usage, "prompt_token_count", None), output_tokens=getattr(usage, "candidates_token_count", None), total_tokens=getattr(usage, "total_token_count", None), retry_count=retries)
