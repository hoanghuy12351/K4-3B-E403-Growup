"""Pure parity tests for the deterministic diagnostic pipeline."""

import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import extract_concepts, generate_diagnostic_check, mine_misconceptions, validate_diagnostic_question


class StubAdapter:
    def get_question_examples_for_concept(self, concepts, limit):
        return [{"turnId": "T00001", "studentQuestion": "What is the difference between a token and a word?"}]


class DiagnosticPipelineTests(unittest.TestCase):
    def test_preserves_the_fixed_phase_one_tokenization_contract(self) -> None:
        context = extract_concepts(title="Tokenization", source_text="A token can be a word, part of a word, or a character.", source_id="slide-12")
        self.assertEqual(context["topic"], "Tokenization")
        self.assertGreater(len(context["concepts"]), 0)
        mined = mine_misconceptions(concepts=["token"], historical_questions=[{"turnId": "T00001", "studentQuestion": "What is the difference between a token and a word?"}])
        self.assertEqual(mined["misconceptions"][0]["evidence"][0]["turnId"], "T00001")
        result = generate_diagnostic_check(
            teaching_context={"title": "Tokenization", "text": "A token can be a word, part of a word, or a character.", "sourceId": "slide-12"},
            options={"historicalQuestionLimit": 2},
            adapter=StubAdapter(),
        )
        self.assertEqual(len(result["questions"]), 1)
        question = result["questions"][0]
        self.assertEqual(question["source"][0]["id"], "slide-12")
        self.assertEqual(sum(option["correct"] for option in question["options"]), 1)
        self.assertTrue(validate_diagnostic_question(question)["valid"])
