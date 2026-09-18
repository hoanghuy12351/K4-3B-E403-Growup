"""Pydantic runtime contract for one LLM diagnostic generation."""

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LLMMisconception(StrictModel):
    id: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    evidenceTurnIds: list[str]


class DiagnosticOption(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    correct: bool
    misconceptionId: str | None


class DiagnosticSource(StrictModel):
    type: str = Field(min_length=1)
    id: str = Field(min_length=1)


class DiagnosticQuestion(StrictModel):
    id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    question: str = Field(min_length=1)
    learningObjective: str = Field(min_length=1)
    source: list[DiagnosticSource] = Field(min_length=1)
    options: list[DiagnosticOption] = Field(min_length=1)


class LLMDiagnosticResult(StrictModel):
    topic: str = Field(min_length=1)
    concepts: list[str] = Field(min_length=1)
    learningObjective: str = Field(min_length=1)
    misconceptions: list[LLMMisconception]
    question: DiagnosticQuestion


class InterpretedTeacherRequest(StrictModel):
    """The bounded assessment requirements inferred from a lecturer prompt."""

    questionCount: int = Field(ge=1, le=10)
    difficulty: str | None 
    style: str | None
    focus: str | None


class LLMCheckpointBatchResult(StrictModel):
    """All checkpoints for one Teaching Agent generation request."""

    interpretedRequest: InterpretedTeacherRequest
    questions: list[DiagnosticQuestion] = Field(min_length=1, max_length=10)


class ProviderResult(StrictModel):
    data: dict
    provider: str
    model: str
    latency_ms: int
    request_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int = 0
