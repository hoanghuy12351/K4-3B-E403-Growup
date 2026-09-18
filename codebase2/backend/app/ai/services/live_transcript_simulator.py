"""Bound canonical transcript evidence for the live classroom demo."""

from app.ai.config import find_repository_root
from app.ai.services.demo_checkpoint_catalog import load_demo_catalog
from app.ai.services.transcript_ingestion import TranscriptIngestionError, TranscriptSegment, parse_transcript_file


class LiveTranscriptError(ValueError):
    """Raised when a live transcript cursor is invalid or moves backwards."""


def load_live_transcript_segments() -> list[TranscriptSegment]:
    """Load the canonical demo transcript once without logging any spoken content."""
    lesson = load_demo_catalog().get("lesson")
    if not isinstance(lesson, dict) or not isinstance(lesson.get("transcriptFile"), str):
        raise LiveTranscriptError("Live transcript configuration is unavailable.")
    path = (find_repository_root() / lesson["transcriptFile"]).resolve()
    try:
        return parse_transcript_file(path)
    except TranscriptIngestionError as error:
        raise LiveTranscriptError("Live transcript evidence is unavailable.") from error


def transcript_positions(segments: list[TranscriptSegment]) -> dict[str, int]:
    """Return stable ref positions while rejecting malformed source data."""
    positions = {segment.ref: index for index, segment in enumerate(segments)}
    if not segments or len(positions) != len(segments):
        raise LiveTranscriptError("Live transcript evidence is invalid.")
    return positions


def visible_segments(segments: list[TranscriptSegment], current_ref: str | None) -> list[TranscriptSegment]:
    """Return only the prefix that has been heard at the current live cursor."""
    if current_ref is None:
        return []
    positions = transcript_positions(segments)
    if current_ref not in positions:
        raise LiveTranscriptError("The transcript cursor is not part of this lesson.")
    return segments[:positions[current_ref] + 1]


def validate_live_cursor(segments: list[TranscriptSegment], *, previous_ref: str | None, next_ref: str) -> None:
    """Allow only known, monotonic transcript progress from the teacher client."""
    positions = transcript_positions(segments)
    if next_ref not in positions:
        raise LiveTranscriptError("The transcript cursor is not part of this lesson.")
    if previous_ref is not None and (previous_ref not in positions or positions[next_ref] < positions[previous_ref]):
        raise LiveTranscriptError("The live transcript cursor cannot move backwards.")
