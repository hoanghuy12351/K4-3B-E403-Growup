"""Deterministic lesson content used by the PDF diagnostic prototype.

The catalog still exposes the local PDF files.  This registry intentionally does
not read their contents, so the diagnostic workflow is stable across machines.
"""

from pathlib import Path
from typing import Any


MOCK_LESSON_CONTENT: dict[str, dict[str, Any]] = {
    "d1-slide-hackathon.pdf": {
        "title": "AI and Prompt Engineering",
        "sections": [
            {
                "title": "Large Language Models",
                "text": "Large language models generate text by predicting tokens based on previous context. A token can represent a word, part of a word, or another text unit.",
            },
            {
                "title": "Prompt Engineering",
                "text": "Prompt engineering is the process of designing instructions and context so that a language model produces useful and reliable outputs.",
            },
            {
                "title": "Tool Calling",
                "text": "Tool calling allows an AI model to request external functions or APIs instead of answering only from model knowledge.",
            },
        ],
    },
    "d2-slide-hackathon.pdf": {
        "title": "Building Reliable AI Learning Experiences",
        "sections": [
            {
                "title": "Grounded AI Responses",
                "text": "Grounded AI responses use supplied lesson material as their source of truth. This makes classroom answers easier to review and verify.",
            },
            {
                "title": "Diagnostic Feedback",
                "text": "A diagnostic question helps a lecturer identify whether students understand a concept before the class moves to the next section.",
            },
            {
                "title": "Human Teaching Decisions",
                "text": "Response summaries can suggest continuing, clarifying, or reteaching. The lecturer remains responsible for the final teaching decision.",
            },
        ],
    },
}


def mock_lesson_for(material_id: str, title: str) -> dict[str, Any]:
    """Return registry content by stable filename, with a transparent fallback."""
    filename = Path(material_id).name.lower()
    material = MOCK_LESSON_CONTENT.get(filename)
    if material:
        return material
    return {
        "title": title,
        "sections": [
            {
                "title": f"{title} — Overview",
                "text": "Mock lesson content used for diagnostic workflow testing. This text is a deterministic fallback and was not extracted from the selected PDF.",
            }
        ],
    }
