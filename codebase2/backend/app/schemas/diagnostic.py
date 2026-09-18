"""HTTP request models for the AI diagnostic endpoint."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

NonEmptyText = Annotated[str, Field(min_length=1)]


class TeachingContextRequest(BaseModel):
    """Teaching material that is passed unchanged to the diagnostic pipeline."""

    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText
    text: NonEmptyText
    source_id: str | None = Field(default=None, alias="sourceId")

    @field_validator("title", "text", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        """Reject whitespace-only required strings after normalizing their edges."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("source_id", mode="before")
    @classmethod
    def strip_optional_source_id(cls, value: object) -> object:
        """Normalize an optional source identifier without inventing one."""
        return value.strip() if isinstance(value, str) else value


class DiagnosticOptionsRequest(BaseModel):
    """Options currently supported by the one-question diagnostic pipeline."""

    model_config = ConfigDict(extra="forbid")

    question_count: int = Field(default=1, alias="questionCount", ge=1, le=1)


class DiagnosticRequest(BaseModel):
    """Public camelCase request contract for a diagnostic generation request."""

    model_config = ConfigDict(extra="forbid")

    teaching_context: TeachingContextRequest = Field(alias="teachingContext")
    options: DiagnosticOptionsRequest | None = None
