"""Bounded, read-only access to the local VLearn evidence pack."""

import csv
import re
from pathlib import Path
from typing import Any, Iterator

from ..config import HISTORICAL_QUESTION_LIMIT, SEARCH_SCAN_LIMIT, find_repository_root


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _tokens(value: object) -> list[str]:
    return re.findall(r"[^\W_]{2,}", _normalize_text(value).lower(), flags=re.UNICODE)


def _discover_dataset_paths(repository_root: Path) -> dict[str, Path | None]:
    data_root = repository_root / "data"
    if not data_root.is_dir():
        return {"dataRoot": data_root, "chatlog": None, "dictionary": None, "transcript": None, "slides": None}
    files = [path for path in data_root.rglob("*") if path.is_file()]
    directories = [path for path in data_root.rglob("*") if path.is_dir()]
    chatlog = next((path for path in files if path.name.lower() == "tutor_turns.csv"), None)
    chatlog_directory = chatlog.parent if chatlog else None
    pack_root = chatlog_directory.parent if chatlog_directory else None
    dictionary = next((path for path in files if chatlog_directory and path.parent == chatlog_directory and path.name.lower() == "data_dictionary.md"), None)
    transcript = next((path for path in directories if pack_root and path.parent == pack_root and path.name.lower() == "transcript"), None)
    slides = next((path for path in directories if pack_root and path.parent == pack_root and path.name.lower() == "slides"), None)
    transcript = transcript or next((path for path in directories if path.name.lower() == "transcript"), None)
    slides = slides or next((path for path in directories if path.name.lower() == "slides"), None)
    return {
        "dataRoot": data_root,
        "chatlog": chatlog,
        "dictionary": dictionary,
        "transcript": transcript,
        "slides": slides,
    }


class VlearnAdapter:
    """Stream normalized VLearn questions without exposing unnecessary raw fields."""

    def __init__(self, repository_root: Path | str | None = None, scan_limit: int = SEARCH_SCAN_LIMIT) -> None:
        self.repository_root = Path(repository_root).resolve() if repository_root else find_repository_root()
        self.scan_limit = scan_limit
        self._paths = _discover_dataset_paths(self.repository_root)

    def _validate_dataset(self) -> None:
        required = ("chatlog", "dictionary", "transcript", "slides")
        missing = [f"{name}: {self._paths[name] or 'not discovered'}" for name in required if not self._paths[name] or not self._paths[name].exists()]
        if missing:
            raise FileNotFoundError(f"VLearn dataset is incomplete. Missing {', '.join(missing)}.")

    def _iter_rows(self) -> Iterator[dict[str, str]]:
        self._validate_dataset()
        chatlog = self._paths["chatlog"]
        assert chatlog is not None
        with chatlog.open("r", encoding="utf-8", newline="") as csv_file:
            yield from csv.DictReader(csv_file)

    @staticmethod
    def _normalize_row(row: dict[str, str]) -> dict[str, str]:
        return {
            "turnId": row.get("turn_id", ""),
            "lectureCode": row.get("lecture_code", ""),
            "lectureTitle": row.get("lecture_title", ""),
            "studentQuestion": _normalize_text(row.get("student_question", "")),
            "askedAt": row.get("asked_at_vn", ""),
            "cohortHint": row.get("cohort_hint", ""),
        }

    @staticmethod
    def _matches_filters(item: dict[str, str], query: object = None, lecture_code: object = None, lecture_title: object = None, cohort_hint: object = None) -> bool:
        if lecture_code and item["lectureCode"].lower() != str(lecture_code).lower():
            return False
        if lecture_title and str(lecture_title).lower() not in item["lectureTitle"].lower():
            return False
        if cohort_hint and item["cohortHint"].lower() != str(cohort_hint).lower():
            return False
        query_terms = _tokens(query)
        if not query_terms:
            return True
        haystack = f"{item['lectureTitle']} {item['studentQuestion']}".lower()
        return all(term in haystack for term in query_terms)

    def get_dataset_info(self) -> dict[str, Any]:
        """Return discovered local resource paths after validating the evidence pack."""
        self._validate_dataset()
        transcript = self._paths["transcript"]
        slides = self._paths["slides"]
        assert transcript is not None and slides is not None
        return {
            "repositoryRoot": str(self.repository_root),
            "dataRoot": str(self._paths["dataRoot"]),
            "chatlogPath": str(self._paths["chatlog"]),
            "dataDictionaryPath": str(self._paths["dictionary"]),
            "transcriptPaths": [str(path) for path in transcript.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".txt"}],
            "slidePaths": [str(path) for path in slides.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"],
        }

    def search_student_questions(self, query: object = None, lecture_code: object = None, lecture_title: object = None, cohort_hint: object = None, limit: int = HISTORICAL_QUESTION_LIMIT) -> list[dict[str, str]]:
        """Return at most 100 matching rows while scanning no more than the configured bound."""
        bounded_limit = max(1, min(int(limit or HISTORICAL_QUESTION_LIMIT), 100))
        results: list[dict[str, str]] = []
        for scanned, row in enumerate(self._iter_rows(), start=1):
            if scanned > self.scan_limit or len(results) >= bounded_limit:
                break
            item = self._normalize_row(row)
            if self._matches_filters(item, query, lecture_code, lecture_title, cohort_hint):
                results.append(item)
        return results

    def get_question_examples_for_concept(self, concepts: list[str] | None, limit: int = HISTORICAL_QUESTION_LIMIT) -> list[dict[str, str]]:
        """Try strict multi-concept matching, then bounded single-concept matching."""
        concepts = [value for value in (concepts or []) if _normalize_text(value)]
        query = " ".join(_normalize_text(value) for value in concepts)
        if not query:
            return []
        strict_matches = self.search_student_questions(query=query, limit=limit)
        if strict_matches:
            return strict_matches
        results: list[dict[str, str]] = []
        for concept in concepts:
            remaining = max(0, limit - len(results))
            if not remaining:
                break
            for match in self.search_student_questions(query=concept, limit=remaining):
                if not any(item["turnId"] == match["turnId"] for item in results):
                    results.append(match)
        return results[:limit]


def create_vlearn_adapter(repository_root: Path | str | None = None, scan_limit: int = SEARCH_SCAN_LIMIT) -> VlearnAdapter:
    """Create the public read-only VLearn adapter."""
    return VlearnAdapter(repository_root=repository_root, scan_limit=scan_limit)
