"""HTTP adapter for the existing AI diagnostic pipeline."""

import logging
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.ai import AISettings, generate_diagnostic_check
from app.ai.llm.errors import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMMalformedResponseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from app.schemas.diagnostic import DiagnosticRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI"])


def _service_unavailable(code: str, message: str) -> JSONResponse:
    """Create a stable error response for unavailable local dependencies."""
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"error": {"code": code, "message": message}})


def _bad_gateway(code: str, message: str, http_status: int = status.HTTP_502_BAD_GATEWAY) -> JSONResponse:
    """Create a stable error response for failed upstream AI operations."""
    return JSONResponse(status_code=http_status, content={"error": {"code": code, "message": message}})


@router.post("/diagnostic")
def create_diagnostic(request: DiagnosticRequest) -> dict[str, Any]:
    """Validate one request and delegate exactly once to the canonical pipeline."""
    teaching_context = request.teaching_context.model_dump(by_alias=True, exclude_none=True)
    options = request.options.model_dump(by_alias=True) if request.options else {}

    try:
        settings = AISettings.from_env()
    except (TypeError, ValueError):
        logger.warning("AI diagnostic configuration is invalid.")
        return _service_unavailable("AI_CONFIGURATION_ERROR", "The AI diagnostic service is not configured correctly.")

    try:
        return generate_diagnostic_check(teaching_context=teaching_context, options=options, settings=settings)
    except FileNotFoundError:
        logger.warning("AI diagnostic dataset is unavailable.")
        return _service_unavailable("AI_DATA_UNAVAILABLE", "The diagnostic dataset is currently unavailable.")
    except LLMConfigurationError:
        logger.warning("AI diagnostic provider configuration is unavailable.")
        return _service_unavailable("AI_PROVIDER_CONFIGURATION_ERROR", "The configured AI provider requires a valid API key and model configuration.")
    except LLMAuthenticationError:
        logger.warning("AI diagnostic provider authentication was rejected.")
        return _service_unavailable("AI_PROVIDER_AUTHENTICATION_ERROR", "The configured AI provider rejected the server credentials.")
    except LLMTimeoutError:
        logger.warning("AI diagnostic provider timed out.")
        return _bad_gateway("AI_PROVIDER_TIMEOUT", "The AI provider timed out while generating a diagnostic question.", status.HTTP_504_GATEWAY_TIMEOUT)
    except (LLMProviderError, LLMRateLimitError, LLMMalformedResponseError, LLMValidationError):
        logger.warning("AI diagnostic provider failed.")
        return _bad_gateway("AI_PROVIDER_ERROR", "The configured AI provider could not generate a diagnostic question.")
    except Exception:
        logger.error("Unexpected AI diagnostic failure.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "The diagnostic service encountered an unexpected error."}},
        )
