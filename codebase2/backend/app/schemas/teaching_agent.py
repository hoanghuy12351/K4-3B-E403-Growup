"""Request contracts for the fixed lesson Teaching Agent demo."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerateDemoCheckpointRequest(BaseModel):
    """Teacher selection of one conceptual section for one checkpoint."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(alias="sectionId", min_length=1, max_length=100)
    expected_students: int | None = Field(default=None, alias="expectedStudents", ge=1, le=10_000)

    @field_validator("section_id", mode="before")
    @classmethod
    def strip_section_id(cls, value: object) -> object:
        """Reject an empty selection after normalizing whitespace."""
        return value.strip() if isinstance(value, str) else value
