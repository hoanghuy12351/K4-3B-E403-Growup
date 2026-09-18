"""Extract text only from explicitly selected PDF pages."""

from pathlib import Path

from pypdf import PdfReader


class SlideEvidenceError(ValueError):
    """Raised when requested PDF slide evidence is unavailable or invalid."""


def _reader(path: Path | str) -> PdfReader:
    candidate = Path(path)
    if not candidate.is_file():
        raise SlideEvidenceError("Slide evidence source is unavailable.")
    try:
        return PdfReader(str(candidate))
    except Exception as error:
        raise SlideEvidenceError("Slide evidence PDF cannot be read.") from error


def pdf_page_count(path: Path | str) -> int:
    """Return the PDF page count for static manifest validation."""
    return len(_reader(path).pages)


def load_slide_evidence(path: Path | str, *, lesson_id: str, page_numbers: list[int] | tuple[int, ...]) -> list[dict[str, object]]:
    """Read selected 1-based pages only and preserve their visible numbering."""
    if not page_numbers:
        raise SlideEvidenceError("At least one slide page must be selected.")
    reader = _reader(path)
    page_count = len(reader.pages)
    evidence = []
    for page_number in page_numbers:
        if not isinstance(page_number, int) or page_number < 1 or page_number > page_count:
            raise SlideEvidenceError("Requested slide page is invalid.")
        text = (reader.pages[page_number - 1].extract_text() or "").strip()
        if not text:
            raise SlideEvidenceError("Requested slide page contains no extractable text.")
        evidence.append({"ref": f"slide:{lesson_id}:{page_number}", "type": "pdf_page", "page": page_number, "text": text})
    return evidence
