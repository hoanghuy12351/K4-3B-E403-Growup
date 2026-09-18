"""Gemini Models API adapter with JSON response format."""

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


from ...config import AISettings
from ..client import retry_transient
from ..errors import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMMalformedResponseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ..models import ProviderResult

UNSUPPORTED_GEMINI_SCHEMA_KEYWORDS = {
    "additionalProperties",
    "additional_properties",
}


def _gemini_schema(value: Any) -> Any:
    """Remove schema keywords unsupported by Google Gemini API."""
    if isinstance(value, list):
        return [_gemini_schema(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _gemini_schema(item)
            for key, item in value.items()
            if key not in UNSUPPORTED_GEMINI_SCHEMA_KEYWORDS
        }
    return value


def _normalize_error(error: Exception) -> Exception:
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
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
    return LLMProviderError(f"Gemini request failed: {error}")


class GeminiProvider:
    """Use the google-genai models.generate_content API with JSON schema format."""

    def __init__(self, settings: AISettings, client: Any = None) -> None:
        if not settings.gemini_api_key or not settings.gemini_model:
            raise LLMConfigurationError("Gemini requires GEMINI_API_KEY and GEMINI_MODEL.")
        self.settings = settings
        if client is None:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
        self.client = client

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: dict, request_id: str) -> ProviderResult:
        """Make one generate_content request and parse text output as JSON."""
        from google.genai import types

        clean_schema = _gemini_schema(schema)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=clean_schema,
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_output_tokens,
        )

        def request() -> Any:
            try:
                return self.client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=user_prompt,
                    config=config,
                )
            except Exception as error:
                raise _normalize_error(error) from error

        started = time.perf_counter()
        logger.info("[Gemini LLM] Đang gọi Google Gemini API (model=%s, request_id=%s)...", self.settings.gemini_model, request_id)
        response, retries = retry_transient(request, self.settings.max_retries)
        output_text = getattr(response, "text", None)
        if not output_text:
            raise LLMMalformedResponseError("Gemini response did not include structured output text.")
        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise LLMMalformedResponseError("Gemini response contained invalid JSON.") from error
        usage = getattr(response, "usage_metadata", None)
        latency_ms = round((time.perf_counter() - started) * 1000)
        logger.info(
            "[Gemini LLM] Thành công! Model=%s, độ trễ=%dms, tokens(in=%s, out=%s, total=%s)",
            self.settings.gemini_model,
            latency_ms,
            getattr(usage, "prompt_token_count", None),
            getattr(usage, "candidates_token_count", None),
            getattr(usage, "total_token_count", None),
        )
        resp_id = getattr(response, "response_id", None) or request_id

        return ProviderResult(
            data=data,
            provider="gemini",
            model=self.settings.gemini_model,
            latency_ms=latency_ms,
            request_id=resp_id,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            total_tokens=getattr(usage, "total_token_count", None),
            retry_count=retries,
        )
