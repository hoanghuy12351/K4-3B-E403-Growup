"""Environment-driven construction of exactly one provider adapter."""

from ..config import AISettings
from .errors import LLMConfigurationError
from .providers import GeminiProvider, NvidiaProvider, OpenAIProvider


def create_provider(settings: AISettings):
    """Create only the selected provider; deterministic mode never calls this factory."""
    if settings.provider == "openai":
        return OpenAIProvider(settings)
    if settings.provider == "gemini":
        return GeminiProvider(settings)
    if settings.provider == "nvidia":
        return NvidiaProvider(settings)
    raise LLMConfigurationError("Unknown AI provider.")
