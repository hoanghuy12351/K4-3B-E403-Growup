"""Deterministic, structure-first segmentation for classroom lesson material."""

import re
from dataclasses import dataclass
from typing import Any

from ..config import LESSON_MAX_SECTIONS, LESSON_SECTION_MAX_CHARS, LESSON_SECTION_MIN_CHARS
from .material_ingestion import IngestedMaterial, SourceBlock


@dataclass(frozen=True)
class LessonSection:
    """A source-traceable, pedagogical lesson section ready for diagnostics."""

    id: str
    title: str
    text: str
    source_refs: list[dict[str, Any]]
    order: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize section fields for API responses."""
        return {"id": self.id, "title": self.title, "text": self.text, "sourceRefs": self.source_refs, "order": self.order}


@dataclass(frozen=True)
class _Chunk:
    """An intermediate structural unit extracted from a source block."""

    title: str | None
    text: str
    source_ref: dict[str, Any]


def _is_heading(line: str) -> bool:
    """Identify explicit headings and concise title-like lines without LLM inference."""
    normalized = line.strip()
    if re.match(r"^#{1,6}\s+\S", normalized):
        return True
    words = normalized.split()
    title_case_words = sum(bool(word[:1].isupper()) for word in words)
    return 1 <= len(words) <= 9 and len(normalized) <= 90 and (
        normalized.isupper()
        or normalized.endswith(":")
        or (not re.search(r"[.!?]$", normalized) and title_case_words >= max(1, len(words) - 2))
    )


def _title_from_block(block: SourceBlock, fallback: str | None) -> str | None:
    """Prefer an explicit heading, otherwise leave title creation to the section fallback."""
    for line in block.text.splitlines()[:4]:
        if _is_heading(line):
            return re.sub(r"^#{1,6}\s*", "", line).rstrip(":").strip()
    return fallback if len(block.text) <= 180 else None


def _split_large_chunk(chunk: _Chunk, maximum_chars: int) -> list[_Chunk]:
    """Bound unusually large sections at paragraph or sentence boundaries."""
    if len(chunk.text) <= maximum_chars:
        return [chunk]
    paragraphs = [item.strip() for item in re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z])", chunk.text) if item.strip()]
    groups: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 1 > maximum_chars:
            groups.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        groups.append(current)
    return [_Chunk(title=chunk.title, text=group, source_ref=chunk.source_ref) for group in groups]


def _structural_chunks(material: IngestedMaterial, maximum_chars: int) -> list[_Chunk]:
    """Create chunks from page and explicit-heading boundaries before any size balancing."""
    chunks: list[_Chunk] = []
    for block in material.blocks:
        reference = {"type": "slide" if block.source_type == "pdf" else "text", "sourceId": block.source_id, "page": block.page}
        lines = block.text.splitlines()
        heading_indexes = [index for index, line in enumerate(lines) if _is_heading(line)]
        if heading_indexes and heading_indexes[0] != 0:
            heading_indexes.insert(0, 0)
        if not heading_indexes:
            title = _title_from_block(block, None)
            chunks.extend(_split_large_chunk(_Chunk(title=title, text=block.text, source_ref=reference), maximum_chars))
            continue
        for position, start in enumerate(heading_indexes):
            end = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(lines)
            text = "\n".join(lines[start:end]).strip()
            if text:
                heading = re.sub(r"^#{1,6}\s*", "", lines[start]).rstrip(":").strip() if _is_heading(lines[start]) else None
                chunks.extend(_split_large_chunk(_Chunk(title=heading, text=text, source_ref=reference), maximum_chars))
    return chunks


def segment_lesson(material: IngestedMaterial, *, min_chars: int = LESSON_SECTION_MIN_CHARS, max_chars: int = LESSON_SECTION_MAX_CHARS, max_sections: int = LESSON_MAX_SECTIONS) -> list[LessonSection]:
    """Merge related adjacent source chunks while preserving heading and page boundaries."""
    if min_chars <= 0 or max_chars < min_chars or max_sections < 1:
        raise ValueError("Lesson segmentation limits are invalid.")
    mock_blocks = [block for block in material.blocks if block.source_type == "mock_pdf"]
    if mock_blocks and len(mock_blocks) == len(material.blocks):
        return [
            LessonSection(
                id=f"section-{order:02d}",
                title=block.section_title or f"{material.title} — Part {order}",
                text=block.text,
                source_refs=[{"type": "mock_pdf", "sourceId": block.source_id, "page": block.page}],
                order=order,
            )
            for order, block in enumerate(mock_blocks[:max_sections], start=1)
        ]
    chunks = _structural_chunks(material, max_chars)
    if not chunks:
        raise ValueError("Lesson material does not contain segmentable text.")
    groups: list[list[_Chunk]] = []
    for chunk in chunks:
        if groups and not chunk.title and len("\n".join(item.text for item in groups[-1])) + len(chunk.text) <= max_chars:
            groups[-1].append(chunk)
        else:
            groups.append([chunk])
    index = 0
    while index < len(groups):
        group_text = "\n".join(item.text for item in groups[index])
        current_has_heading = any(item.title for item in groups[index])
        previous_has_heading = any(item.title for item in groups[index - 1]) if index > 0 else False
        if len(group_text) < min_chars and index > 0 and not (current_has_heading and previous_has_heading) and len("\n".join(item.text for item in groups[index - 1])) + len(group_text) <= max_chars:
            groups[index - 1].extend(groups.pop(index))
            continue
        index += 1
    while len(groups) > max_sections:
        smallest_index = min(range(len(groups) - 1), key=lambda item: len("\n".join(chunk.text for chunk in groups[item])) + len("\n".join(chunk.text for chunk in groups[item + 1])))
        combined_size = len("\n".join(chunk.text for chunk in groups[smallest_index])) + len("\n".join(chunk.text for chunk in groups[smallest_index + 1]))
        if combined_size > max_chars:
            break
        groups[smallest_index].extend(groups.pop(smallest_index + 1))
    sections: list[LessonSection] = []
    for order, group in enumerate(groups, start=1):
        title = next((item.title for item in group if item.title), f"{material.title} — Part {order}")
        source_refs = [item.source_ref for item in group]
        sections.append(LessonSection(id=f"section-{order:02d}", title=title, text="\n".join(item.text for item in group), source_refs=source_refs, order=order))
    return sections
