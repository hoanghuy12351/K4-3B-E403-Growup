"""Runtime LLM checkpoint generation grounded in only heard lecture evidence."""

import json
import time
import uuid
from typing import Any

from app.ai.config import AISettings
from app.ai.llm.errors import LLMConfigurationError
from app.ai.llm.factory import create_provider
from app.ai.llm.models import LLMCheckpointBatchResult
from app.ai.services.llm_checkpoint_batch_service import _validate_batch
from app.ai.services.transcript_ingestion import TranscriptSegment


SYSTEM_PROMPT = """
Bạn là Growup Teaching Agent tạo checkpoint cho một buổi học trực tiếp bằng tiếng Việt.
Chỉ kiểm tra nội dung đã được giảng trong SLIDE_EVIDENCE và LIVE_TRANSCRIPT_EVIDENCE.
Không suy luận hoặc kiểm tra kiến thức từ phần bài giảng chưa xuất hiện.
Mỗi câu hỏi có đúng bốn đáp án và đúng một đáp án đúng. Tuân thủ yêu cầu của giảng viên.
Trả về structured output theo schema được yêu cầu.
"""


def build_live_checkpoint_prompt(*, teacher_prompt: str, current_slide: int, section: dict[str, Any], slide_evidence: list[dict[str, Any]], transcript_evidence: list[TranscriptSegment], analysis: dict[str, Any]) -> str:
    """Build the provider prompt from bounded live evidence, never the full transcript."""
    payload = {
        "currentSlide": current_slide,
        "checkpointSection": section,
        "concepts": analysis["concepts"],
        "learningObjectives": analysis["learningObjectives"],
        "misconceptions": analysis["misconceptions"],
        "allowedSourceRefs": analysis["allowedSourceRefs"],
    }
    transcript = [{"ref": item.ref, "text": item.text} for item in transcript_evidence]
    return "\n".join([
        "<LECTURER_REQUEST>", teacher_prompt, "</LECTURER_REQUEST>",
        "<CURRENT_CLASS_STATE>", json.dumps({"currentSlide": current_slide, "visibleTranscriptUntil": transcript[-1]["ref"] if transcript else None}, ensure_ascii=False), "</CURRENT_CLASS_STATE>",
        "<SECTION_METADATA>", json.dumps(payload, ensure_ascii=False), "</SECTION_METADATA>",
        "<SLIDE_EVIDENCE>", json.dumps(slide_evidence, ensure_ascii=False), "</SLIDE_EVIDENCE>",
        "<LIVE_TRANSCRIPT_EVIDENCE>", json.dumps(transcript, ensure_ascii=False), "</LIVE_TRANSCRIPT_EVIDENCE>",
        "<TASK>", "Generate the requested checkpoint questions using only the provided evidence and source references.", "</TASK>",
    ])


def generate_live_checkpoint_batch(*, teacher_prompt: str, current_slide: int, section: dict[str, Any], slide_evidence: list[dict[str, Any]], transcript_evidence: list[TranscriptSegment], analysis: dict[str, Any], settings: AISettings, provider: Any = None) -> tuple[LLMCheckpointBatchResult, dict[str, Any]]:
    """Make one real configured-provider request and locally validate its output."""
    if settings.mode == "deterministic":
        raise LLMConfigurationError("Live checkpoint generation requires an LLM provider.")
    provider = provider or create_provider(settings)
    started = time.perf_counter()
    result = provider.generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_live_checkpoint_prompt(teacher_prompt=teacher_prompt, current_slide=current_slide, section=section, slide_evidence=slide_evidence, transcript_evidence=transcript_evidence, analysis=analysis),
        schema=LLMCheckpointBatchResult.model_json_schema(),
        request_id=str(uuid.uuid4()),
    )
    batch = _validate_batch(json.loads(json.dumps(result.data)), analysis)
    return batch, {
        "mode": "llm_live_runtime",
        "provider": result.provider,
        "model": result.model,
        "latencyMs": result.latency_ms or round((time.perf_counter() - started) * 1000),
        "fallbackUsed": False,
        "fallbackReason": None,
        "retryCount": result.retry_count,
        "usage": {"inputTokens": result.input_tokens, "outputTokens": result.output_tokens, "totalTokens": result.total_tokens},
        "interpretedRequest": batch.interpretedRequest.model_dump(),
    }
