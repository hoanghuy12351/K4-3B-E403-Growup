"""NVIDIA NIM OpenAI-compatible adapter with local JSON validation."""

import json
import time
from typing import Any

from ...config import AISettings
from ..client import retry_transient
from ..errors import LLMAuthenticationError, LLMConfigurationError, LLMMalformedResponseError, LLMProviderError, LLMRateLimitError, LLMTimeoutError
from ..models import ProviderResult


def _strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```") and text.endswith("```"):
        return text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return text


def _normalize_error(error: Exception) -> Exception:
    status = getattr(error, "status_code", None)
    if isinstance(error, TimeoutError):
        return LLMTimeoutError("NVIDIA request timed out.")
    if status in {401, 403}:
        return LLMAuthenticationError("NVIDIA authentication was rejected.")
    if status == 429:
        return LLMRateLimitError("NVIDIA rate limit was reached.")
    if status == 400:
        return LLMConfigurationError("NVIDIA rejected the request configuration.")
    if status in {408, 500, 502, 503, 504}:
        return LLMProviderError("NVIDIA request failed temporarily.")
    return LLMProviderError("NVIDIA request failed.")


class NvidiaProvider:
    """Call the selected NVIDIA NIM style without hidden endpoint switching."""

    def __init__(self, settings: AISettings, client: Any = None) -> None:
        if not settings.nvidia_api_key or not settings.nvidia_model or not settings.nvidia_base_url:
            raise LLMConfigurationError("NVIDIA requires NVIDIA_API_KEY, NVIDIA_MODEL, and NVIDIA_BASE_URL.")
        self.settings = settings
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=settings.nvidia_api_key, base_url=settings.nvidia_base_url, timeout=settings.timeout_seconds)
        self.client = client

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: dict, request_id: str) -> ProviderResult:
        """Use configured chat completions or Responses style and validate JSON locally."""
        def request() -> Any:
            try:
                if self.settings.nvidia_api_style == "responses":
                    return self.client.responses.create(model=self.settings.nvidia_model, instructions=system_prompt, input=user_prompt, max_output_tokens=self.settings.max_output_tokens, temperature=self.settings.temperature, store=False)
                return self.client.chat.completions.create(
                    model=self.settings.nvidia_model,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_output_tokens,
                    stream=False,
                )
            except Exception as error:
                raise _normalize_error(error) from error

        started = time.perf_counter()
        response, retries = retry_transient(request, self.settings.max_retries)
        if self.settings.nvidia_api_style == "responses":
            output_text = getattr(response, "output_text", None)
        else:
            choices = getattr(response, "choices", [])
            output_text = getattr(getattr(choices[0], "message", None), "content", None) if choices else None
        if not output_text:
            raise LLMMalformedResponseError("NVIDIA response did not include JSON content.")
        try:
            data = json.loads(_strip_code_fence(output_text))
        except json.JSONDecodeError as error:
            raise LLMMalformedResponseError("NVIDIA response contained invalid JSON.") from error
        usage = getattr(response, "usage", None)
        return ProviderResult(data=data, provider="nvidia", model=self.settings.nvidia_model, latency_ms=round((time.perf_counter() - started) * 1000), request_id=getattr(response, "id", request_id), input_tokens=getattr(usage, "prompt_tokens", None), output_tokens=getattr(usage, "completion_tokens", None), total_tokens=getattr(usage, "total_tokens", None), retry_count=retries)
