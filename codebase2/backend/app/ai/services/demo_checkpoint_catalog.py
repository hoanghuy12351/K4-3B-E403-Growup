"""Load the fixed offline checkpoint fixtures for the preset classroom demo."""

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


class DemoCheckpointCatalogError(ValueError):
    """Raised when a required preset demo fixture is missing or malformed."""


_DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
_CATALOG_PATH = _DATA_DIRECTORY / "demo_lesson_catalog.json"
_CHECKPOINTS_PATH = _DATA_DIRECTORY / "demo_checkpoints.json"
PRESET_CHECKPOINT_COUNT = 3


@lru_cache(maxsize=1)
def _load_fixtures() -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse local JSON fixtures once without opening source PDFs or transcripts."""
    try:
        catalog = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
        checkpoints = json.loads(_CHECKPOINTS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise DemoCheckpointCatalogError("Preset demo fixtures are unavailable.") from error
    if not isinstance(catalog, dict) or not isinstance(checkpoints, dict):
        raise DemoCheckpointCatalogError("Preset demo fixtures have an invalid root shape.")
    return catalog, checkpoints


def load_demo_catalog() -> dict[str, Any]:
    """Return a copy of the teacher-selection fixture."""
    catalog, _ = _load_fixtures()
    return deepcopy(catalog)


def list_demo_sections() -> list[dict[str, Any]]:
    """Return the eight configured section records in fixture order."""
    sections = load_demo_catalog().get("sections")
    if not isinstance(sections, list):
        raise DemoCheckpointCatalogError("Preset demo catalog has no sections.")
    return sections


def get_demo_section(section_id: str) -> dict[str, Any]:
    """Return one configured section without accessing lesson source files."""
    normalized_id = str(section_id or "").strip()
    for section in list_demo_sections():
        if isinstance(section, dict) and section.get("id") == normalized_id:
            return section
    raise KeyError(normalized_id)


def get_demo_checkpoint(section_id: str) -> dict[str, Any]:
    """Return the prepared checkpoint matching one section identifier."""
    _, checkpoints = _load_fixtures()
    checkpoint = checkpoints.get(str(section_id or "").strip())
    if not isinstance(checkpoint, dict):
        raise KeyError(section_id)
    return deepcopy(checkpoint)


def _section_source_refs(section: dict[str, Any], question_refs: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert fixture references into the existing source-ref shape without dropping provenance."""
    lesson = load_demo_catalog().get("lesson")
    if not isinstance(lesson, dict) or not isinstance(lesson.get("id"), str):
        raise DemoCheckpointCatalogError("Preset demo lesson metadata is invalid.")
    pages = section.get("slidePages")
    refs = section.get("transcriptRefs")
    if not isinstance(pages, list) or not isinstance(refs, list):
        raise DemoCheckpointCatalogError("Preset demo section evidence is invalid.")
    configured_refs = [
        *[{"type": "pdf_page", "id": f"slide:{lesson['id']}:{page}"} for page in pages if isinstance(page, int)],
        *[{"type": "transcript", "id": ref} for ref in refs if isinstance(ref, str)],
    ]
    result = list(configured_refs)
    known_refs = {(item["type"], item["id"]) for item in configured_refs}
    for item in question_refs:
        if not isinstance(item, dict):
            continue
        reference = (item.get("type"), item.get("id"))
        if isinstance(reference[0], str) and isinstance(reference[1], str) and reference not in known_refs:
            result.append({"type": reference[0], "id": reference[1]})
            known_refs.add(reference)
    return result


def build_demo_session_section(section_id: str) -> dict[str, Any]:
    """Adapt one immutable preset into the existing DiagnosticSession section shape."""
    section = get_demo_section(section_id)
    checkpoint = get_demo_checkpoint(section_id)
    question = checkpoint.get("question")
    if not isinstance(question, dict) or checkpoint.get("sectionId") != section.get("id"):
        raise DemoCheckpointCatalogError("Preset demo checkpoint does not match its section.")
    if question.get("id") != section.get("checkpointId"):
        raise DemoCheckpointCatalogError("Preset demo checkpoint ID is invalid.")
    options = question.get("options")
    if not isinstance(options, list) or len(options) != 4 or sum(item.get("correct") is True for item in options if isinstance(item, dict)) != 1:
        raise DemoCheckpointCatalogError("Preset demo checkpoint options are invalid.")
    misconception_ids = {item.get("id") for item in checkpoint.get("misconceptions", []) if isinstance(item, dict)}
    if any(item.get("misconceptionId") not in misconception_ids for item in options if isinstance(item, dict) and item.get("misconceptionId")):
        raise DemoCheckpointCatalogError("Preset demo checkpoint has an unknown misconception.")
    question_refs = question.get("source")
    if not isinstance(question_refs, list) or not all(isinstance(item, dict) and isinstance(item.get("type"), str) and isinstance(item.get("id"), str) for item in question_refs):
        raise DemoCheckpointCatalogError("Preset demo checkpoint has an invalid source reference.")
    source_refs = _section_source_refs(section, question_refs)
    return {
        "sectionId": section["id"],
        "section": {
            "id": section["id"],
            "title": section["title"],
            "order": section["order"],
            "sourceRefs": source_refs,
        },
        "concepts": checkpoint.get("concepts", []),
        "learningObjectives": checkpoint.get("learningObjectives", []),
        "misconceptions": checkpoint.get("misconceptions", []),
        "historicalEvidence": {"matchedQuestions": 0},
        "question": question,
        "generation": checkpoint.get("generation", {}),
    }


def build_demo_session_sections(section_id: str) -> list[dict[str, Any]]:
    """Create three distinct preset checkpoints for one selected concept section."""
    template = build_demo_session_section(section_id)
    base_question = template["question"]
    if not isinstance(base_question, dict):
        raise DemoCheckpointCatalogError("Preset demo question is invalid.")
    base_question_id = str(base_question["id"])
    base_section_id = str(template["section"]["id"])
    concept = str(base_question.get("concept") or template["section"]["title"])
    question_texts = [
        str(base_question["question"]),
        f"Phát biểu nào phù hợp nhất với nội dung bài giảng về {concept}?",
        f"Khi kiểm tra hiểu biết về {concept}, lựa chọn nào bám sát nhất nội dung đã học?",
    ][:PRESET_CHECKPOINT_COUNT]
    sections = []
    for index, question_text in enumerate(question_texts, start=1):
        item = deepcopy(template)
        item["sectionId"] = f"{base_section_id}-q{index:02d}"
        item["section"]["id"] = item["sectionId"]
        item["section"]["title"] = f"{template['section']['title']} — Câu {index}"
        item["question"]["id"] = f"{base_question_id}-{index:02d}"
        item["question"]["question"] = question_text
        sections.append(item)
    return sections
