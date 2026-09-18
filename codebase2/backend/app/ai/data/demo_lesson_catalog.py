"""Read and validate the fixed, backend-owned demo lesson catalog."""

from dataclasses import dataclass
import json
from pathlib import Path

from ..config import find_repository_root
from ..services.slide_evidence import pdf_page_count
from ..services.transcript_ingestion import parse_transcript_file


class DemoLessonCatalogError(ValueError):
    """Raised when the static demo lesson catalog is incomplete or invalid."""


@dataclass(frozen=True)
class DemoSection:
    """A verified conceptual section with source references only."""

    id: str
    title: str
    slide_pages: tuple[int, ...]
    transcript_from: str
    transcript_to: str
    order: int


@dataclass(frozen=True)
class DemoLesson:
    """A fixed demo lesson and its independently selectable sections."""

    id: str
    title: str
    slide_path: str
    transcript_path: str
    sections: tuple[DemoSection, ...]


def _manifest_path() -> Path:
    return Path(__file__).with_name("demo_lessons.json")


def _required_text(value: object, field: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise DemoLessonCatalogError(f"Demo lesson catalog requires {field}.")
    return result


def _read_catalog() -> DemoLesson:
    try:
        payload = json.loads(_manifest_path().read_text(encoding="utf-8"))
        lessons = payload["lessons"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise DemoLessonCatalogError("Demo lesson catalog cannot be read.") from error
    if not isinstance(lessons, list) or len(lessons) != 1:
        raise DemoLessonCatalogError("Demo lesson catalog must contain exactly one lesson.")
    lesson = lessons[0]
    if not isinstance(lesson, dict):
        raise DemoLessonCatalogError("Demo lesson catalog lesson is invalid.")
    sections: list[DemoSection] = []
    for order, item in enumerate(lesson.get("sections") or [], start=1):
        if not isinstance(item, dict):
            raise DemoLessonCatalogError("Demo lesson section is invalid.")
        refs = item.get("transcriptRefs")
        if not isinstance(refs, dict):
            raise DemoLessonCatalogError("Demo lesson section requires transcript references.")
        pages = tuple(item.get("slidePages") or [])
        if not pages or any(not isinstance(page, int) for page in pages):
            raise DemoLessonCatalogError("Demo lesson section requires valid slide pages.")
        sections.append(DemoSection(
            id=_required_text(item.get("id"), "section id"),
            title=_required_text(item.get("title"), "section title"),
            slide_pages=pages,
            transcript_from=_required_text(refs.get("from"), "transcript range start"),
            transcript_to=_required_text(refs.get("to"), "transcript range end"),
            order=order,
        ))
    return DemoLesson(
        id=_required_text(lesson.get("id"), "lesson id"),
        title=_required_text(lesson.get("title"), "lesson title"),
        slide_path=_required_text(lesson.get("slidePath"), "slide path"),
        transcript_path=_required_text(lesson.get("transcriptPath"), "transcript path"),
        sections=tuple(sections),
    )


def _source_path(relative_path: str) -> Path:
    candidate = (find_repository_root() / relative_path).resolve()
    try:
        candidate.relative_to(find_repository_root().resolve() / "data")
    except ValueError as error:
        raise DemoLessonCatalogError("Demo lesson source must be inside the data directory.") from error
    return candidate


def validate_demo_lesson() -> DemoLesson:
    """Validate every static source reference before it is used as evidence."""
    lesson = _read_catalog()
    if not lesson.sections:
        raise DemoLessonCatalogError("Demo lesson must contain at least one section.")
    section_ids = [section.id for section in lesson.sections]
    if len(section_ids) != len(set(section_ids)):
        raise DemoLessonCatalogError("Demo lesson section IDs must be unique.")
    slide_path = _source_path(lesson.slide_path)
    transcript_path = _source_path(lesson.transcript_path)
    if not slide_path.is_file() or not transcript_path.is_file():
        raise DemoLessonCatalogError("Demo lesson evidence source is unavailable.")
    page_count = pdf_page_count(slide_path)
    segments = parse_transcript_file(transcript_path)
    refs = [segment.ref for segment in segments]
    ref_positions = {ref: index for index, ref in enumerate(refs)}
    for section in lesson.sections:
        if not section.title or not section.slide_pages:
            raise DemoLessonCatalogError("Demo lesson section has no slide evidence.")
        if not section.transcript_from or not section.transcript_to:
            raise DemoLessonCatalogError("Demo lesson section has no transcript evidence.")
        if any(page < 1 or page > page_count for page in section.slide_pages):
            raise DemoLessonCatalogError(f"Demo lesson section {section.id} has an invalid slide page.")
        if section.transcript_from not in ref_positions or section.transcript_to not in ref_positions:
            raise DemoLessonCatalogError(f"Demo lesson section {section.id} has an unknown transcript reference.")
        if ref_positions[section.transcript_from] > ref_positions[section.transcript_to]:
            raise DemoLessonCatalogError(f"Demo lesson section {section.id} has an unordered transcript range.")
    return lesson


def get_demo_lesson() -> DemoLesson:
    """Return the only supported demo lesson after source validation."""
    return validate_demo_lesson()


def list_demo_sections() -> list[DemoSection]:
    """Return the teacher-selectable conceptual sections in source order."""
    return list(get_demo_lesson().sections)


def get_demo_section(section_id: str) -> DemoSection:
    """Return one section without accepting an arbitrary lesson or source path."""
    normalized_id = str(section_id or "").strip()
    lesson = get_demo_lesson()
    for section in lesson.sections:
        if section.id == normalized_id:
            return section
    raise KeyError(normalized_id)
