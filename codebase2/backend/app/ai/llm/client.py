"""Bounded retry helpers shared by provider adapters."""

import random
import time
from collections.abc import Callable
from typing import TypeVar

from .errors import LLMError, LLMProviderError, LLMRateLimitError, LLMTimeoutError

T = TypeVar("T")
TRANSIENT_ERRORS = (LLMProviderError, LLMRateLimitError, LLMTimeoutError)


def retry_transient(call: Callable[[], T], max_retries: int) -> tuple[T, int]:
    """Retry only normalized transient errors with bounded exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return call(), attempt
        except TRANSIENT_ERRORS:
            if attempt >= max_retries:
                raise
            time.sleep(min(1.0, 0.1 * (2 ** attempt)) + random.uniform(0, 0.05))
        except LLMError:
            raise
    raise AssertionError("Retry loop should return or raise.")
