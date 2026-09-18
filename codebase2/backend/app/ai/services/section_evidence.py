"""Build normalized, section-scoped evidence from the static demo catalog."""

from dataclasses import dataclass
from ..config import find_repository_root
from ..data.demo_lesson_catalog import DemoLesson, DemoSection, get_demo_lesson, get_demo_section
from .slide_evidence import load_slide_evidence
from .transcript_ingestion import parse_transcript_file, select_transcript_segments


@dataclass(frozen=True)
class SectionEvidence:
    """The complete and isolated evidence bundle for one selected section."""

    lesson_id: str
    section_id: str
    title: str
    slide_evidence: list[dict[str, object]]
    transcript_evidence: list[dict[str, str]]

    @property
    def source_refs(self) -> list[dict[str, str]]:
        """Return canonical provenance records without exposing text to clients."""
        return [
            *[{"type": "pdf_page", "id": str(item["ref"])} for item in self.slide_evidence],
            *[{"type": "transcript_segment", "id": item["ref"]} for item in self.transcript_evidence],
        ]


def build_section_evidence(section_id: str) -> SectionEvidence:
    """Load only the selected section's declared slide and transcript evidence."""
    lesson: DemoLesson = get_demo_lesson()
    section: DemoSection = get_demo_section(section_id)
    root = find_repository_root()
    slides = load_slide_evidence(root / lesson.slide_path, lesson_id=lesson.id, page_numbers=section.slide_pages)
    segments = parse_transcript_file(root / lesson.transcript_path)
    selected = select_transcript_segments(segments, from_ref=section.transcript_from, to_ref=section.transcript_to)
    return SectionEvidence(
        lesson_id=lesson.id,
        section_id=section.id,
        title=section.title,
        slide_evidence=slides,
        transcript_evidence=[{"ref": segment.ref, "text": segment.text} for segment in selected],
    )
