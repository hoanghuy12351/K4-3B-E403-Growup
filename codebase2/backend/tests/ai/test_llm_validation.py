"""Pure grounding validation tests for structured model output."""

import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.llm.errors import LLMValidationError
from app.ai.llm.validation import parse_and_validate


def payload(evidence_id="T00001", source_id="slide-12"):
    return {"topic": "Tokenization", "concepts": ["Tokenization"], "learningObjective": "Explain tokenization.", "misconceptions": [{"id": "M001", "concept": "Tokenization", "statement": "Possible historical confusion.", "evidenceTurnIds": [evidence_id]}], "question": {"id": "Q1", "topic": "Tokenization", "concept": "Tokenization", "question": "Which statement is supported?", "learningObjective": "Explain tokenization.", "source": [{"type": "slide", "id": source_id}], "options": [{"id": "A", "text": "A token can be a word.", "correct": True, "misconceptionId": None}, {"id": "B", "text": "A possible confusion.", "correct": False, "misconceptionId": "M001"}]}}


class LLMValidationTests(unittest.TestCase):
    def test_accepts_grounded_contract(self):
        result = parse_and_validate(payload(), evidence_turn_ids={"T00001"}, teaching_context={"title": "Tokenization", "text": "A token can be a word.", "sourceId": "slide-12"})
        self.assertEqual(result.question.id, "Q1")

    def test_rejects_invented_evidence_and_source_ids(self):
        context = {"title": "Tokenization", "text": "A token can be a word.", "sourceId": "slide-12"}
        with self.assertRaises(LLMValidationError):
            parse_and_validate(payload(evidence_id="T99999"), evidence_turn_ids={"T00001"}, teaching_context=context)
        with self.assertRaises(LLMValidationError):
            parse_and_validate(payload(source_id="invented-slide"), evidence_turn_ids={"T00001"}, teaching_context=context)
