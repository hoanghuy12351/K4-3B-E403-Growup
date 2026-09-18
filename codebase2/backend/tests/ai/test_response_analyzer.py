"""Pure tests for deterministic response aggregation."""

import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import analyze_responses


class ResponseAnalyzerTests(unittest.TestCase):
    def test_maps_wrong_options_to_misconception_signals(self) -> None:
        result = analyze_responses(
            question={"concept": "retrieval", "options": [{"id": "A", "correct": False, "misconceptionId": "M001"}, {"id": "B", "correct": True, "misconceptionId": None}]},
            responses=[{"optionId": "A"}, {"optionId": "A"}, {"optionId": "B"}],
        )
        self.assertEqual(result["totalResponses"], 3)
        self.assertEqual(result["correctRate"], 0.333)
        self.assertEqual(result["status"], "needs_attention")
        self.assertEqual(result["misconceptionSignals"], [{"misconceptionId": "M001", "count": 2, "ratio": 0.667}])
