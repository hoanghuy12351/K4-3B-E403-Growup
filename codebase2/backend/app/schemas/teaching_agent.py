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


class GenerateAgentCheckpointRequest(BaseModel):
    """Natural-language lecturer request for grounded demo checkpoint generation."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(alias="sectionId", min_length=1, max_length=100)
    teacher_request: str = Field(alias="teacherRequest", min_length=1, max_length=2_000)
    expected_students: int | None = Field(default=None, alias="expectedStudents", ge=1, le=10_000)

    @field_validator("section_id", "teacher_request", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        """Normalize required text and let field constraints reject blank values."""
        return value.strip() if isinstance(value, str) else value


class LiveCheckpointSelection(BaseModel):
    """One lecturer-selected future checkpoint in the canonical demo lesson."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(alias="sectionId", min_length=1, max_length=100)
    teacher_prompt: str = Field(alias="teacherPrompt", min_length=1, max_length=2_000)
    trigger_slide: int | None = Field(default=None, alias="triggerSlide", ge=1, le=100)

    @field_validator("section_id", "teacher_prompt", mode="before")
    @classmethod
    def strip_live_selection_text(cls, value: object) -> object:
        """Normalize selected section IDs and lecturer instructions."""
        return value.strip() if isinstance(value, str) else value


class CreateLiveSessionRequest(BaseModel):
    """Create a live session plan without generating questions in advance."""

    model_config = ConfigDict(extra="forbid")

    lesson_id: str = Field(alias="lessonId", min_length=1, max_length=100)
    expected_students: int | None = Field(default=None, alias="expectedStudents", ge=1, le=10_000)
    checkpoint_selections: list[LiveCheckpointSelection] = Field(alias="checkpointSelections", min_length=1, max_length=8)

    @field_validator("lesson_id", mode="before")
    @classmethod
    def strip_lesson_id(cls, value: object) -> object:
        """Reject whitespace-only lesson identifiers."""
        return value.strip() if isinstance(value, str) else value
