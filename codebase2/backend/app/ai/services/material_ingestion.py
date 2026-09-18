"""Normalize raw lesson text or a local slide PDF into source-aware text blocks."""

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any

from ..config import find_repository_root
from ..data.mock_lesson_materials import mock_lesson_for


class MaterialIngestionError(ValueError):
    """Raised when supplied lesson material cannot be safely normalized."""


@dataclass(frozen=True)
class SourceBlock:
    """One ordered source unit retained for later segmentation traceability."""

    page: int
    text: str
    source_id: str
    source_type: str
    section_title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the source block using the API's camelCase contract."""
        result = {"page": self.page, "text": self.text, "sourceId": self.source_id, "type": self.source_type}
        if self.section_title:
            result["sectionTitle"] = self.section_title
        return result


@dataclass(frozen=True)
class IngestedMaterial:
    """Normalized lesson material with stable source identity and blocks."""

    title: str
    source_id: str
    blocks: list[SourceBlock]


@dataclass(frozen=True)
class AvailableMaterial:
    """A safe metadata record for a selectable PDF in the local evidence pack."""

    id: str
    title: str
    source_id: str
    pdf_path: str

    def to_dict(self) -> dict[str, str]:
        """Expose only display metadata and a repository-relative material identifier."""
        return {"id": self.id, "title": self.title, "sourceId": self.source_id, "type": "pdf"}


def _normalize_text(value: object) -> str:
    """Collapse whitespace while preserving paragraph breaks as structural signals."""
    lines = [" ".join(line.split()) for line in str(value or "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _resolve_pdf_path(pdf_path: str) -> Path:
    """Allow PDF ingestion only from the repository's read-only data directory."""
    repository_root = find_repository_root()
    data_root = (repository_root / "data").resolve()
    candidate = Path(pdf_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (repository_root / candidate).resolve()
    try:
        resolved.relative_to(data_root)
    except ValueError as error:
        raise MaterialIngestionError("pdfPath must reference a PDF inside the local data directory.") from error
    if resolved.suffix.lower() != ".pdf" or not resolved.is_file():
        raise MaterialIngestionError("The requested lesson PDF is unavailable.")
    return resolved


def _material_title(path: Path) -> str:
    """Convert a local PDF filename into a readable dropdown label."""
    return " ".join(part.capitalize() for part in path.stem.replace("_", "-").split("-"))


def list_available_materials() -> list[AvailableMaterial]:
    """List only local PDF lessons under data without exposing absolute paths."""
    repository_root = find_repository_root()
    data_root = repository_root / "data"
    if not data_root.is_dir():
        raise FileNotFoundError("The local data directory is unavailable.")
    materials = []
    for path in sorted(data_root.rglob("*.pdf")):
        relative_path = path.relative_to(repository_root).as_posix()
        source_id = f"pdf-{sha1(relative_path.encode('utf-8')).hexdigest()[:12]}"
        materials.append(AvailableMaterial(id=relative_path, title=_material_title(path), source_id=source_id, pdf_path=relative_path))
    return materials


def resolve_available_material(material_id: str) -> dict[str, str]:
    """Resolve a dropdown identifier instead of accepting a client-controlled filesystem path."""
    material = next((item for item in list_available_materials() if item.id == material_id), None)
    if material is None:
        raise MaterialIngestionError("The selected lesson material is unavailable.")
    return {"materialId": material.id, "title": material.title, "sourceId": material.source_id, "pdfPath": material.pdf_path}


def _ingest_mock_pdf(title: str, source_id: str, pdf_path: str) -> IngestedMaterial:
    """Map a selected local PDF to explicitly mock extracted blocks.

    Validating the path preserves the existing local-material boundary, but the
    PDF bytes are never opened or parsed in the diagnostic workflow.
    """
    _resolve_pdf_path(pdf_path)
    mock_lesson = mock_lesson_for(pdf_path, title)
    blocks = [
        SourceBlock(
            page=index,
            text=_normalize_text(section["text"]),
            source_id=source_id,
            source_type="mock_pdf",
            section_title=_normalize_text(section["title"]),
        )
        for index, section in enumerate(mock_lesson["sections"], start=1)
    ]
    return IngestedMaterial(title=_normalize_text(mock_lesson["title"]), source_id=source_id, blocks=blocks)


def ingest_material(material: dict[str, Any]) -> IngestedMaterial:
    """Normalize supported material inputs while keeping their source references."""
    title = _normalize_text(material.get("title"))
    source_id = _normalize_text(material.get("sourceId"))
    text = _normalize_text(material.get("text"))
    pdf_path = _normalize_text(material.get("pdfPath"))
    if not title or not source_id:
        raise MaterialIngestionError("Lesson title and sourceId are required.")
    if text and pdf_path:
        raise MaterialIngestionError("Provide either text or pdfPath, not both.")
    if text:
        return IngestedMaterial(title=title, source_id=source_id, blocks=[SourceBlock(page=1, text=text, source_id=source_id, source_type="text")])
    if pdf_path:
        return _ingest_mock_pdf(title, source_id, pdf_path)
    raise MaterialIngestionError("Lesson material requires non-empty text or pdfPath.")
