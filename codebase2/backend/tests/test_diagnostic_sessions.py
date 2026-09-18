"""End-to-end tests for the mock-PDF diagnostic session workflow."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.services.lesson_diagnostic_service import SectionDiagnostic
from app.ai.services.lesson_segmenter import LessonSection, segment_lesson
from app.ai.services.material_ingestion import ingest_material, list_available_materials, resolve_available_material
from app.diagnostic.aggregation import build_class_summary
from app.diagnostic.models import DiagnosticSession, StudentResponse
from app.main import app


def section_diagnostic() -> SectionDiagnostic:
    """Create a provider-free, reviewable question for HTTP workflow tests."""
    section = LessonSection(
        id="section-01",
        title="Large Language Models",
        text="Large language models predict tokens from context.",
        source_refs=[{"type": "mock_pdf", "sourceId": "pdf-test", "page": 1}],
        order=1,
    )
    return SectionDiagnostic(
        section=section,
        concepts=["Large Language Models"],
        learning_objectives=["Explain large language models."],
        misconceptions=[],
        historical_evidence={"matchedQuestions": 0},
        question={
            "id": "Q-section-01",
            "topic": "Large Language Models",
            "concept": "Large Language Models",
            "question": "What do large language models predict?",
            "learningObjective": "Explain large language models.",
            "source": [{"type": "mock_pdf", "id": "pdf-test"}],
            "options": [
                {"id": "A", "text": "Tokens from previous context.", "correct": True, "misconceptionId": None},
                {"id": "B", "text": "Only complete dictionary words.", "correct": False, "misconceptionId": None},
                {"id": "C", "text": "Random external APIs.", "correct": False, "misconceptionId": None},
            ],
        },
        generation={"mode": "llm"},
    )


class MockMaterialTests(unittest.TestCase):
    def test_selected_pdf_resolves_to_mock_blocks_and_sections(self) -> None:
        material = next(item for item in list_available_materials() if item.id.endswith("d1-slide-hackathon.pdf"))
        resolved = resolve_available_material(material.id)
        ingested = ingest_material(resolved)

        self.assertEqual(ingested.title, "AI and Prompt Engineering")
        self.assertEqual(ingested.source_id, material.source_id)
        self.assertTrue(ingested.blocks)
        self.assertTrue(all(block.source_type == "mock_pdf" for block in ingested.blocks))
        sections = segment_lesson(ingested)
        self.assertEqual([section.title for section in sections], ["Large Language Models", "Prompt Engineering", "Tool Calling"])
        self.assertEqual(len(sections), len(ingested.blocks))


class DiagnosticSessionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.generation_patch = patch("app.diagnostic.service.generate_lesson_diagnostic", return_value=[section_diagnostic()])
        self.generation_patch.start()
        self.addCleanup(self.generation_patch.stop)

    def test_draft_start_student_safe_answers_and_latest_replacement(self) -> None:
        material_id = next(item.id for item in list_available_materials() if item.id.endswith("d1-slide-hackathon.pdf"))
        created = self.client.post("/api/diagnostic-sessions", json={"lesson": {"materialId": material_id}, "expectedStudents": 5})
        self.assertEqual(created.status_code, 201)
        session = created.json()
        self.assertEqual(session["status"], "draft")
        self.assertEqual(session["lesson"]["materialId"], material_id)
        self.assertEqual(session["lesson"]["contentMode"], "mock_pdf_extract")
        self.assertEqual(len(session["sections"]), 1)
        session_id = session["sessionId"]

        safe_session = self.client.get(f"/api/diagnostic-sessions/{session_id}")
        self.assertEqual(safe_session.status_code, 200)
        self.assertNotIn("correct", safe_session.text)
        self.assertEqual(self.client.post(f"/api/diagnostic-sessions/{session_id}/start").json()["status"], "active")

        payload = {"studentId": "student-001", "questionId": "Q-section-01", "sectionId": "section-01", "optionId": "A"}
        self.assertEqual(self.client.post(f"/api/diagnostic-sessions/{session_id}/responses", json=payload).status_code, 201)
        payload["optionId"] = "B"
        self.assertEqual(self.client.post(f"/api/diagnostic-sessions/{session_id}/responses", json=payload).status_code, 201)
        summary = self.client.get(f"/api/diagnostic-sessions/{session_id}/summary").json()
        self.assertEqual(summary["sectionResults"][0]["totalResponses"], 1)
        self.assertEqual(summary["sectionResults"][0]["incorrectResponses"], 1)


class RecommendationTests(unittest.TestCase):
    def _summary_for_answers(self, correct_answers: int, total_answers: int) -> dict:
        diagnostic = section_diagnostic().to_dict()
        session = DiagnosticSession(id="test-session", lesson={"title": "Test", "sourceId": "pdf-test"}, sections=[diagnostic], expected_students=total_answers)
        option_id = "A"
        for number in range(total_answers):
            session.responses.append(StudentResponse(
                id=f"response-{number}", session_id=session.id, question_id="Q-section-01", section_id="section-01",
                student_id=f"student-{number}", option_id=option_id if number < correct_answers else "B",
            ))
        return build_class_summary(session)

    def test_recommendation_thresholds(self) -> None:
        self.assertEqual(self._summary_for_answers(5, 5)["recommendation"], "continue")
        self.assertEqual(self._summary_for_answers(3, 5)["recommendation"], "clarify")
        self.assertEqual(self._summary_for_answers(2, 5)["recommendation"], "reteach")
        self.assertEqual(self._summary_for_answers(1, 1)["recommendation"], "insufficient_data")
