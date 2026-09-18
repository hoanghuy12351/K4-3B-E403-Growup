"""Provider-neutral interface for structured generation."""

from typing import Protocol

from .models import ProviderResult


class LLMProvider(Protocol):
    """Minimal provider boundary; business logic stays outside provider modules."""

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: dict, request_id: str) -> ProviderResult:
        """Return parsed JSON and safe request metadata."""
