"""Sanitized error types for server-side LLM operations."""


class LLMError(Exception):
    """Base error that deliberately contains only safe diagnostic text."""


class LLMConfigurationError(LLMError):
    """Required provider configuration is absent or invalid."""


class LLMAuthenticationError(LLMError):
    """Provider rejected credentials without exposing them."""


class LLMRateLimitError(LLMError):
    """Provider rate limit response."""


class LLMTimeoutError(LLMError):
    """Provider request exceeded the configured deadline."""


class LLMProviderError(LLMError):
    """Safe normalization for provider or temporary transport failures."""


class LLMMalformedResponseError(LLMError):
    """Provider response was incomplete or could not be parsed as JSON."""


class LLMValidationError(LLMError):
    """Provider output failed local contract or grounding validation."""
