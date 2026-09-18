"""HTTP schemas for the multi-section diagnostic-session workflow."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonEmptyText = Annotated[str, Field(min_length=1)]


class LessonMaterialRequest(BaseModel):
    """Lesson input accepts a catalog selection or the existing explicit material form."""

    model_config = ConfigDict(extra="forbid")

    material_id: str | None = Field(default=None, alias="materialId")
    title: NonEmptyText | None = None
    source_id: NonEmptyText | None = Field(default=None, alias="sourceId")
    text: str | None = None
    pdf_path: str | None = Field(default=None, alias="pdfPath")

    @field_validator("material_id", "title", "source_id", "text", "pdf_path", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        """Normalize string edges so whitespace-only lesson fields are invalid."""
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_exactly_one_material_source(self) -> "LessonMaterialRequest":
        """Ensure ingestion has one well-defined material source."""
        if self.material_id:
            if self.title or self.source_id or self.text or self.pdf_path:
                raise ValueError("materialId cannot be combined with manual lesson fields.")
            return self
        if not self.title or not self.source_id:
            raise ValueError("Manual lesson input requires title and sourceId.")
        if bool(self.text) == bool(self.pdf_path):
            raise ValueError("Provide exactly one of lesson.text or lesson.pdfPath.")
        return self


class CreateDiagnosticSessionRequest(BaseModel):
    """Lecturer request for a generated diagnostic session."""

    model_config = ConfigDict(extra="forbid")

    lesson: LessonMaterialRequest
    expected_students: int | None = Field(default=None, alias="expectedStudents", ge=1, le=10_000)


class StudentResponseRequest(BaseModel):
    """A student option selection for one session question."""

    model_config = ConfigDict(extra="forbid")

    student_id: NonEmptyText = Field(alias="studentId")
    question_id: NonEmptyText = Field(alias="questionId")
    section_id: NonEmptyText = Field(alias="sectionId")
    option_id: NonEmptyText = Field(alias="optionId")

    @field_validator("student_id", "question_id", "section_id", "option_id", mode="before")
    @classmethod
    def strip_identifiers(cls, value: object) -> object:
        """Reject identifiers containing only whitespace."""
        return value.strip() if isinstance(value, str) else value
