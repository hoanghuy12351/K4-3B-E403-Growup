"""Parse clean transcript Markdown into ordered, private evidence segments."""

from dataclasses import dataclass
from pathlib import Path
import re


class TranscriptIngestionError(ValueError):
    """Raised when a clean transcript cannot provide requested evidence."""


@dataclass(frozen=True)
class TranscriptSegment:
    """One canonical transcript segment retaining its stable source reference."""

    ref: str
    text: str


_SEGMENT_PATTERN = re.compile(r"\*\*\[(T\d{2}-\d{3})\]\*\*\s*")


def parse_transcript(text: str) -> list[TranscriptSegment]:
    """Parse ordered Markdown segments without changing lecturer wording."""
    matches = list(_SEGMENT_PATTERN.finditer(text))
    if not matches:
        raise TranscriptIngestionError("Transcript contains no canonical segment identifiers.")
    segments = []
    for index, match in enumerate(matches):
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():body_end].strip()
        if not body:
            raise TranscriptIngestionError(f"Transcript segment {match.group(1)} is empty.")
        segments.append(TranscriptSegment(ref=match.group(1), text=body))
    refs = [segment.ref for segment in segments]
    if len(refs) != len(set(refs)):
        raise TranscriptIngestionError("Transcript contains duplicate segment identifiers.")
    return segments


def parse_transcript_file(path: Path | str) -> list[TranscriptSegment]:
    """Load one known clean transcript file without logging its content."""
    candidate = Path(path)
    if not candidate.is_file():
        raise TranscriptIngestionError("Transcript evidence source is unavailable.")
    return parse_transcript(candidate.read_text(encoding="utf-8"))


def select_transcript_segments(segments: list[TranscriptSegment], *, refs: list[str] | None = None, from_ref: str | None = None, to_ref: str | None = None) -> list[TranscriptSegment]:
    """Select an explicit ref list or one inclusive, ordered segment range."""
    positions = {segment.ref: index for index, segment in enumerate(segments)}
    if refs is not None:
        if not refs or any(ref not in positions for ref in refs):
            raise TranscriptIngestionError("Requested transcript reference is unavailable.")
        return [segments[positions[ref]] for ref in refs]
    if not from_ref or not to_ref or from_ref not in positions or to_ref not in positions:
        raise TranscriptIngestionError("Requested transcript range is unavailable.")
    start, end = positions[from_ref], positions[to_ref]
    if start > end:
        raise TranscriptIngestionError("Requested transcript range is not ordered.")
    return segments[start:end + 1]
