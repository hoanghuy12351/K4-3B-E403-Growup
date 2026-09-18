"""Request and response contracts for learner-answer classification."""

from typing import Literal

from pydantic import BaseModel, Field


ClassificationLabel = Literal[
    "understood", "partial", "misunderstood", "unclear", "teacher_review"
]


class ClassificationRequest(BaseModel):
    session_id: str = Field(min_length=1, alias="sessionId")
    question_id: str = Field(min_length=1, alias="questionId")
    answer: str = Field(max_length=10_000)

    model_config = {"populate_by_name": True, "extra": "forbid"}


class ClassificationResponse(BaseModel):
    label: ClassificationLabel
    misconceptions: list[str]
    source_refs: list[str]
    needs_teacher_review: bool
    security_event: Literal["prompt_injection_detected"] | None = None


class BatchClassificationRequest(BaseModel):
    items: list[ClassificationRequest] = Field(min_length=1, max_length=100)


class BatchClassificationResponse(BaseModel):
    items: list[ClassificationResponse]
