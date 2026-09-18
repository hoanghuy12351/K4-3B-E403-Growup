"""AI settings, deterministic defaults, and repository discovery."""

import os
from dataclasses import dataclass
from pathlib import Path

HISTORICAL_QUESTION_LIMIT = 30
QUESTION_COUNT = 1
SEARCH_SCAN_LIMIT = 15_000
RESPONSE_THRESHOLDS = {"understood": 0.80, "uncertain": 0.60}


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_backend_env(env_file: Path | str | None = None) -> None:
    """Load simple KEY=VALUE pairs from backend/.env without overwriting exported variables."""
    path = Path(env_file) if env_file else Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#") or "=" not in candidate:
            continue
        key, value = candidate.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class AISettings:
    """Centralized server-side configuration for deterministic and LLM modes."""

    mode: str = "hybrid"
    provider: str = "openai"
    fallback_to_deterministic: bool = True
    timeout_seconds: float = 25.0
    max_retries: int = 2
    max_output_tokens: int = 1800
    temperature: float = 0.2
    max_historical_questions: int = 20
    max_evidence_chars: int = 300
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    nvidia_api_key: str | None = None
    nvidia_model: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_style: str = "chat_completions"

    def __post_init__(self) -> None:
        if self.mode not in {"deterministic", "llm", "hybrid"}:
            raise ValueError("AI_MODE must be deterministic, llm, or hybrid.")
        if self.provider not in {"openai", "gemini", "nvidia"}:
            raise ValueError("AI_PROVIDER must be openai, gemini, or nvidia.")
        if self.nvidia_api_style not in {"chat_completions", "responses"}:
            raise ValueError("NVIDIA_API_STYLE must be chat_completions or responses.")
        if self.timeout_seconds <= 0 or self.max_retries < 0 or self.max_output_tokens <= 0:
            raise ValueError("AI timeout, retry count, and output token limit must be positive.")

    @classmethod
    def from_env(cls, env_file: Path | str | None = None) -> "AISettings":
        """Load backend/.env then build settings without exposing secrets in results."""
        load_backend_env(env_file)
        env = os.environ
        return cls(
            mode=env.get("AI_MODE", "hybrid").lower(),
            provider=env.get("AI_PROVIDER", "openai").lower(),
            fallback_to_deterministic=_as_bool(env.get("AI_FALLBACK_TO_DETERMINISTIC"), True),
            timeout_seconds=float(env.get("AI_TIMEOUT_SECONDS", "25")),
            max_retries=int(env.get("AI_MAX_RETRIES", "2")),
            max_output_tokens=int(env.get("AI_MAX_OUTPUT_TOKENS", "1800")),
            temperature=float(env.get("AI_TEMPERATURE", "0.2")),
            max_historical_questions=int(env.get("AI_MAX_HISTORICAL_QUESTIONS", "20")),
            max_evidence_chars=int(env.get("AI_MAX_EVIDENCE_CHARS", "300")),
            openai_api_key=env.get("OPENAI_API_KEY") or None,
            openai_model=env.get("OPENAI_MODEL") or None,
            openai_base_url=env.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            gemini_api_key=env.get("GEMINI_API_KEY") or None,
            gemini_model=env.get("GEMINI_MODEL") or None,
            gemini_base_url=env.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
            nvidia_api_key=env.get("NVIDIA_API_KEY") or None,
            nvidia_model=env.get("NVIDIA_MODEL") or None,
            nvidia_base_url=env.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            nvidia_api_style=env.get("NVIDIA_API_STYLE", "chat_completions").lower(),
        )


def find_repository_root(start_directory: Path | str | None = None) -> Path:
    """Find the repository root without relying on a machine-specific path."""
    current = Path(start_directory or __file__).resolve()
    if current.is_file():
        current = current.parent
    while current != current.parent:
        if (current / "data").is_dir() and (current / "codebase2").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("Could not locate repository root containing data/ and codebase2/.")
