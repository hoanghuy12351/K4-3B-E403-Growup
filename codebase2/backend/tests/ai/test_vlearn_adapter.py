"""Local integration tests for the read-only VLearn adapter."""

import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import create_vlearn_adapter


class VlearnAdapterTests(unittest.TestCase):
    @unittest.skipUnless((BACKEND_ROOT.parents[1] / "data").is_dir(), "local data/ pack is unavailable")
    def test_discovers_and_returns_bounded_normalized_questions(self) -> None:
        adapter = create_vlearn_adapter()
        info = adapter.get_dataset_info()
        self.assertTrue(info["chatlogPath"].endswith("tutor_turns.csv"))
        self.assertGreaterEqual(len(info["transcriptPaths"]), 1)
        self.assertGreaterEqual(len(info["slidePaths"]), 1)
        rows = adapter.search_student_questions(lecture_code="D01", limit=2)
        self.assertGreater(len(rows), 0)
        self.assertLessEqual(len(rows), 2)
        self.assertEqual(list(rows[0]), ["turnId", "lectureCode", "lectureTitle", "studentQuestion", "askedAt", "cohortHint"])
