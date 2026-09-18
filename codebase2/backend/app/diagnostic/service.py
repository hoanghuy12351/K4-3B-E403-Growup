"""Application service that joins AI generation with session-state workflow."""

from typing import Any
from secrets import choice
from uuid import uuid4

from app.ai.config import AISettings
from app.ai.services.lesson_diagnostic_service import generate_lesson_diagnostic
from app.ai.services.material_ingestion import ingest_material, resolve_available_material
from app.ai.services.answer_classification_service import classify_explanation
from app.ai.services.demo_checkpoint_catalog import build_demo_session_sections, get_demo_section, load_demo_catalog
from app.ai.services.demo_slide_analysis import get_preanalyzed_section
from app.ai.services.live_checkpoint_generation import generate_live_checkpoint_batch
from app.ai.services.live_transcript_simulator import load_live_transcript_segments, transcript_positions, validate_live_cursor, visible_segments
from app.ai.services.slide_evidence import load_slide_evidence
from app.ai.config import find_repository_root
from app.domain.classification import ClassificationDecision, rubric_from_diagnostic

from .aggregation import build_class_summary
from .models import DiagnosticSession, StudentResponse
from .repository import DiagnosticSessionRepository, SessionNotFoundError


class SessionValidationError(ValueError):
    """Raised when a student response does not match its generated session."""


class DiagnosticSessionService:
    """Coordinate material ingestion, per-section AI calls, and transient storage."""

    def __init__(self, repository: DiagnosticSessionRepository) -> None:
        self.repository = repository

    def create_session(self, lesson: dict[str, Any], expected_students: int | None, teacher_id: str | None = None, settings: AISettings | None = None) -> DiagnosticSession:
        """Generate one diagnostic per section and save the session as lecturer-reviewable draft."""
        if lesson.get("materialId") and not lesson.get("sourceBlocks"):
            lesson = resolve_available_material(str(lesson["materialId"]))
        material = ingest_material(lesson)
        section_diagnostics = generate_lesson_diagnostic(material, settings=settings)
        session = DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson={
                "materialId": lesson.get("materialId"),
                "title": material.title,
                "sourceId": material.source_id,
                "contentMode": "mock_pdf_extract" if all(block.source_type == "mock_pdf" for block in material.blocks) else "text",
                "sourceBlocks": [block.to_dict() for block in material.blocks],
            },
            sections=[item.to_dict() for item in section_diagnostics],
            expected_students=expected_students,
        )
        return self.repository.create_session(session)

    def create_section_session(self, *, lesson: dict[str, Any], checkpoint: dict[str, Any], expected_students: int | None, teacher_id: str) -> DiagnosticSession:
        """Create a draft session containing exactly one pre-scoped checkpoint."""
        if not checkpoint.get("section") or not checkpoint.get("question"):
            raise SessionValidationError("A demo checkpoint must include one section and one question.")
        return self.repository.create_session(DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson=lesson,
            sections=[checkpoint],
            expected_students=expected_students,
        ))

    def create_preset_demo_session(self, *, teacher_id: str, section_id: str, expected_students: int | None) -> DiagnosticSession:
        """Create one static, offline demo session without runtime AI or source parsing."""
        catalog = load_demo_catalog()
        lesson = catalog.get("lesson")
        section = get_demo_section(section_id)
        if not isinstance(lesson, dict):
            raise SessionValidationError("Preset demo lesson metadata is invalid.")
        return self.repository.create_session(DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson={
                "id": lesson["id"],
                "materialId": lesson["id"],
                "title": lesson["title"],
                "sourceId": lesson["id"],
                "contentMode": "preset_demo",
                "slideSource": "d1-slide-hackathon.pdf",
                "transcriptSource": "transcript-04-clean.md",
                "selectedSectionId": section["id"],
            },
            sections=build_demo_session_sections(section_id),
            expected_students=expected_students,
        ))

    def create_agent_demo_session(self, *, teacher_id: str, analysis: dict[str, Any], sections: list[dict[str, Any]], expected_students: int | None) -> DiagnosticSession:
        """Persist generated, reviewable demo questions from pre-analyzed lesson data."""
        lesson = analysis["lesson"]
        selected = analysis["section"]
        return self.repository.create_session(DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson={
                "id": lesson["id"],
                "materialId": lesson["id"],
                "title": lesson["title"],
                "sourceId": lesson["id"],
                "contentMode": "preanalyzed_demo",
                "selectedSectionId": selected["id"],
            },
            sections=sections,
            expected_students=expected_students,
        ))

    def create_live_session(self, *, teacher_id: str, lesson_id: str, selections: list[dict[str, Any]], expected_students: int | None) -> DiagnosticSession:
        """Persist an ordered live plan without making any LLM request."""
        catalog = load_demo_catalog()
        lesson = catalog.get("lesson")
        if not isinstance(lesson, dict) or lesson.get("id") != lesson_id:
            raise SessionValidationError("The requested demo lesson was not found.")
        seen: set[str] = set()
        plans: list[dict[str, Any]] = []
        for selection in selections:
            section_id = str(selection.get("sectionId") or "")
            if section_id in seen:
                raise SessionValidationError("A section may only be selected once.")
            seen.add(section_id)
            try:
                section = get_demo_section(section_id)
            except KeyError as error:
                raise SessionValidationError("The requested checkpoint section was not found.") from error
            pages = section.get("slidePages")
            refs = section.get("transcriptRefs")
            if not isinstance(pages, list) or not pages or not isinstance(refs, list) or not refs:
                raise SessionValidationError("Checkpoint source metadata is invalid.")
            trigger_slide = selection.get("triggerSlide") or max(pages)
            if trigger_slide not in pages:
                raise SessionValidationError("The trigger slide must belong to its selected section.")
            teacher_prompt = str(selection.get("teacherPrompt") or "").strip()
            if not teacher_prompt:
                raise SessionValidationError("A lecturer prompt is required for every checkpoint.")
            plans.append({
                "id": f"cp-{section_id}",
                "sectionId": section_id,
                "sectionTitle": section["title"],
                "order": section["order"],
                "slidePages": pages,
                "triggerSlide": trigger_slide,
                "requiredTranscriptRef": refs[-1],
                "teacherPrompt": teacher_prompt,
                "status": "planned",
                "questionIds": [],
            })
        plans.sort(key=lambda plan: int(plan["order"]))
        return self.repository.create_session(DiagnosticSession(
            id=str(uuid4()),
            teacher_id=teacher_id,
            room_code=self._room_code(),
            lesson={
                "id": lesson["id"], "materialId": lesson["id"], "title": lesson["title"], "sourceId": lesson["id"],
                "contentMode": "live_transcript_demo", "slideSource": lesson["slideFile"], "transcriptSource": lesson["transcriptFile"],
            },
            sections=[],
            expected_students=expected_students,
            checkpoint_plans=plans,
        ))

    def update_live_state(self, session_id: str, *, current_slide: int, current_transcript_ref: str) -> DiagnosticSession:
        """Store validated, monotonic presenter progress without trusting transcript text."""
        session = self.get_session(session_id)
        if session.lesson.get("contentMode") != "live_transcript_demo":
            raise SessionValidationError("This session does not use the live transcript flow.")
        if current_slide < session.current_slide:
            raise SessionValidationError("The live slide cursor cannot move backwards.")
        catalog = load_demo_catalog()
        sections = catalog.get("sections")
        if not isinstance(sections, list):
            raise SessionValidationError("Live lesson metadata is unavailable.")
        all_pages = [page for section in sections if isinstance(section, dict) for page in section.get("slidePages", []) if isinstance(page, int)]
        if current_slide < 1 or current_slide > max(all_pages, default=0):
            raise SessionValidationError("The current slide is not part of the demo lesson.")
        segments = load_live_transcript_segments()
        positions = transcript_positions(segments)
        validate_live_cursor(segments, previous_ref=session.current_transcript_ref, next_ref=current_transcript_ref)
        eligible = [section for section in sections if isinstance(section, dict) and current_slide <= max(section.get("slidePages") or [0])]
        max_ref = eligible[0].get("transcriptRefs", [])[-1] if eligible else segments[-1].ref
        if not isinstance(max_ref, str) or positions[current_transcript_ref] > positions[max_ref]:
            raise SessionValidationError("The transcript cursor is ahead of the current slide.")
        session.current_slide = current_slide
        session.current_transcript_ref = current_transcript_ref
        return session

    def trigger_live_checkpoint(self, session_id: str, plan_id: str, *, settings: AISettings, provider: Any = None) -> tuple[DiagnosticSession, dict[str, Any], bool]:
        """Generate one checkpoint at its reached boundary and atomically expose valid questions."""
        session = self.get_session(session_id)
        if session.lesson.get("contentMode") != "live_transcript_demo":
            raise SessionValidationError("This session does not use the live checkpoint flow.")
        plan = next((item for item in session.checkpoint_plans if item["id"] == plan_id), None)
        if plan is None:
            raise SessionValidationError("The checkpoint plan does not belong to this session.")
        if plan["status"] in {"generating", "open", "closed"}:
            return session, plan, False
        if session.current_slide < plan["triggerSlide"] or session.current_transcript_ref is None:
            raise SessionValidationError("This checkpoint has not been reached yet.")
        segments = load_live_transcript_segments()
        positions = transcript_positions(segments)
        if positions[session.current_transcript_ref] < positions[plan["requiredTranscriptRef"]]:
            raise SessionValidationError("The required lecture transcript has not been heard yet.")
        earlier = [item for item in session.checkpoint_plans if item["order"] < plan["order"]]
        if any(item["status"] in {"planned", "generating", "open"} for item in earlier):
            raise SessionValidationError("Close earlier checkpoints before opening the next one.")
        plan["status"] = "generating"
        try:
            analysis = get_preanalyzed_section(str(plan["sectionId"]))
            heard = visible_segments(segments, session.current_transcript_ref)
            slide_path = (find_repository_root() / str(session.lesson["slideSource"])).resolve()
            catalog = load_demo_catalog()
            catalog_sections = catalog.get("sections")
            pages = sorted({
                page
                for item in catalog_sections if isinstance(item, dict)
                for page in item.get("slidePages", [])
                if isinstance(page, int) and page <= session.current_slide
            }) if isinstance(catalog_sections, list) else []
            if not pages:
                raise SessionValidationError("No covered slide evidence is available for this checkpoint.")
            slides = load_slide_evidence(slide_path, lesson_id=str(session.lesson["id"]), page_numbers=pages)
            analysis = {
                **analysis,
                "allowedSourceRefs": [
                    *[{"type": "pdf_page", "id": str(item["ref"])} for item in slides],
                    *[{"type": "transcript", "id": item.ref} for item in heard],
                ],
            }
            batch, generation = generate_live_checkpoint_batch(
                teacher_prompt=str(plan["teacherPrompt"]), current_slide=session.current_slide,
                section={"id": plan["sectionId"], "title": plan["sectionTitle"], "triggerSlide": plan["triggerSlide"]},
                slide_evidence=slides, transcript_evidence=heard, analysis=analysis, settings=settings, provider=provider,
            )
            new_sections = []
            for index, question in enumerate(batch.questions, start=1):
                question_data = question.model_dump()
                question_id = f"{plan['id']}-q{index:02d}-{uuid4().hex[:8]}"
                section_id = f"{plan['id']}-section-{index:02d}"
                question_data["id"] = question_id
                new_sections.append({
                    "sectionId": section_id,
                    "section": {"id": section_id, "originalSectionId": plan["sectionId"], "title": f"{plan['sectionTitle']} — Câu {index}", "order": int(plan["order"]) * 100 + index, "sourceRefs": analysis["allowedSourceRefs"]},
                    "concepts": analysis["concepts"], "learningObjectives": analysis["learningObjectives"], "misconceptions": analysis["misconceptions"],
                    "historicalEvidence": {"matchedQuestions": 0}, "question": question_data, "generation": generation,
                })
            session.sections.extend(new_sections)
            plan["questionIds"] = [item["question"]["id"] for item in new_sections]
            plan["status"] = "open"
            session.status = "live"
            session.active_question_ids = list(plan["questionIds"])
            session.active_question_id = session.active_question_ids[0] if session.active_question_ids else None
            return session, plan, True
        except Exception:
            plan["status"] = "failed"
            plan["questionIds"] = []
            raise

    def close_live_checkpoint(self, session_id: str, plan_id: str) -> DiagnosticSession:
        """Close all questions produced by one live plan before resuming the lesson."""
        session = self.get_session(session_id)
        plan = next((item for item in session.checkpoint_plans if item["id"] == plan_id), None)
        if plan is None or plan["status"] != "open":
            raise SessionValidationError("The requested live checkpoint is not open.")
        ids = set(plan["questionIds"])
        session.active_question_ids = [item for item in session.active_question_ids if item not in ids]
        session.active_question_id = session.active_question_ids[0] if session.active_question_ids else None
        plan["status"] = "closed"
        return session

    def _room_code(self) -> str:
        """Generate a short public code while keeping the UUID internal."""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(20):
            code = "GX-" + "".join(choice(alphabet) for _ in range(4))
            try:
                self.repository.get_session_by_room_code(code)
            except SessionNotFoundError:
                return code
        raise RuntimeError("Could not generate a unique room code.")

    def get_session(self, session_id: str) -> DiagnosticSession:
        """Read a session through the replaceable persistence boundary."""
        return self.repository.get_session(session_id)

    def require_teacher(self, session_id: str, teacher_id: str) -> DiagnosticSession:
        """Ensure one authenticated teacher cannot control another teacher's session."""
        session = self.get_session(session_id)
        if session.teacher_id and session.teacher_id != teacher_id:
            raise SessionValidationError("This classroom belongs to another teacher.")
        return session

    def start_session(self, session_id: str) -> DiagnosticSession:
        """Mark lecturer-reviewed draft material as available for student responses."""
        session = self.get_session(session_id)
        session.status = "ready"
        return session

    def join_room(self, room_code: str, display_name: str) -> dict[str, str]:
        """Create a transient anonymous participant without creating a user account."""
        session = self.repository.get_session_by_room_code(room_code.strip().upper())
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("The classroom is not available for joining yet.")
        participant_id = f"anon_{uuid4().hex[:12]}"
        session.participants[participant_id] = display_name.strip()
        return {"participantId": participant_id, "sessionId": session.id, "roomCode": session.room_code}

    def room_state(self, room_code: str, participant_id: str) -> dict[str, Any]:
        """Return only the active question and public classroom state to a joined student."""
        session = self.repository.get_session_by_room_code(room_code.strip().upper())
        if participant_id not in session.participants:
            raise SessionValidationError("The participant is not joined to this room.")
        active_sections = [item for item in session.sections if item["question"]["id"] in session.active_question_ids]
        questions = []
        for active in active_sections:
            questions.append({
                **{key: value for key, value in active["question"].items() if key not in {"options", "correct", "rubric"}},
                "sectionId": active["section"]["id"],
                "options": [{key: value for key, value in option.items() if key not in {"correct", "misconceptionId"}} for option in active["question"]["options"]],
            })
        return {
            "sessionId": session.id,
            "roomCode": session.room_code,
            "status": session.status,
            "activeQuestion": questions[0] if questions else None,
            "activeQuestions": questions,
        }

    def open_checkpoint(self, session_id: str, question_id: str) -> DiagnosticSession:
        """Open exactly one generated checkpoint for a live classroom."""
        session = self.get_session(session_id)
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("Start the classroom before opening a checkpoint.")
        if not any(item["question"]["id"] == question_id for item in session.sections):
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        session.status = "live"
        session.active_question_id = question_id
        session.active_question_ids = [question_id]
        return session

    def open_all_checkpoints(self, session_id: str) -> DiagnosticSession:
        """Open every generated checkpoint so students can answer the full set."""
        session = self.get_session(session_id)
        if session.status not in {"ready", "live"}:
            raise SessionValidationError("Start the classroom before opening checkpoints.")
        question_ids = [str(item["question"]["id"]) for item in session.sections]
        if not question_ids:
            raise SessionValidationError("This diagnostic session has no checkpoints.")
        session.status = "live"
        session.active_question_id = question_ids[0]
        session.active_question_ids = question_ids
        return session

    def close_checkpoint(self, session_id: str, question_id: str) -> DiagnosticSession:
        """Hide the active checkpoint while leaving the classroom live."""
        session = self.get_session(session_id)
        if question_id not in session.active_question_ids:
            raise SessionValidationError("The requested checkpoint is not open.")
        session.active_question_ids = [item for item in session.active_question_ids if item != question_id]
        session.active_question_id = session.active_question_ids[0] if session.active_question_ids else None
        return session

    def close_all_checkpoints(self, session_id: str) -> DiagnosticSession:
        """Hide every checkpoint while preserving all submitted responses."""
        session = self.get_session(session_id)
        session.active_question_id = None
        session.active_question_ids = []
        return session

    def submit_response(self, session_id: str, participant_id: str, question_id: str, section_id: str, option_id: str, explanation: str | None = None) -> StudentResponse:
        """Validate session ownership then save the student's latest answer to that question."""
        session = self.get_session(session_id)
        if session.status != "live" or question_id not in session.active_question_ids:
            raise SessionValidationError("This checkpoint is not open for responses.")
        if participant_id not in session.participants:
            raise SessionValidationError("The participant is not joined to this classroom.")
        question_section = next((item for item in session.sections if item["question"]["id"] == question_id), None)
        if question_section is None:
            raise SessionValidationError("The question does not belong to this diagnostic session.")
        if question_section["section"]["id"] != section_id:
            raise SessionValidationError("The section does not match the selected question.")
        if not any(option.get("id") == option_id for option in question_section["question"].get("options", [])):
            raise SessionValidationError("The selected option does not belong to this question.")
        selected_option = next(option for option in question_section["question"]["options"] if option.get("id") == option_id)
        classification = None
        if explanation:
            if session.lesson.get("contentMode") in {"preset_demo", "preanalyzed_demo"}:
                classification = self._preset_classification(question_section, selected_option).to_dict()
            else:
                rubric = rubric_from_diagnostic(question_section)
                classification = classify_explanation(rubric=rubric, explanation=explanation, settings=AISettings.from_env()).to_dict()
        response = StudentResponse(
            id=str(uuid4()),
            session_id=session.id,
            question_id=question_id,
            section_id=section_id,
            participant_id=participant_id,
            option_id=option_id,
            explanation=explanation,
            correct=bool(selected_option.get("correct")),
            classification=classification,
        )
        return self.repository.save_response(response)

    @staticmethod
    def _preset_classification(question_section: dict[str, Any], option: dict[str, Any]) -> ClassificationDecision:
        """Classify preset-demo answers deterministically without provider access."""
        refs = tuple(str(item.get("id")) for item in question_section["section"].get("sourceRefs", []) if isinstance(item, dict) and item.get("id"))
        if option.get("correct") is True:
            return ClassificationDecision("understood", (), refs, False)
        misconception_id = option.get("misconceptionId")
        if isinstance(misconception_id, str) and misconception_id:
            return ClassificationDecision("misunderstood", (misconception_id,), refs, False)
        return ClassificationDecision("partial", (), refs, False)

    def summary(self, session_id: str) -> dict[str, Any]:
        """Build a non-identifying lecturer summary from the stored session responses."""
        return build_class_summary(self.get_session(session_id))

    def teacher_view(self, session: DiagnosticSession) -> dict[str, Any]:
        """Return lecturer controls plus only the transcript prefix already revealed."""
        payload = self.student_view(session)
        payload.update({
            "checkpointPlans": session.checkpoint_plans,
            "currentSlide": session.current_slide,
            "currentTranscriptRef": session.current_transcript_ref,
            "visibleTranscript": [{"ref": item.ref, "text": item.text} for item in visible_segments(load_live_transcript_segments(), session.current_transcript_ref)] if session.lesson.get("contentMode") == "live_transcript_demo" else [],
        })
        if session.lesson.get("contentMode") == "live_transcript_demo":
            segments = load_live_transcript_segments()
            positions = transcript_positions(segments)
            next_index = positions[session.current_transcript_ref] + 1 if session.current_transcript_ref else 0
            catalog = load_demo_catalog()
            catalog_sections = catalog.get("sections")
            eligible = [item for item in catalog_sections if isinstance(item, dict) and session.current_slide <= max(item.get("slidePages") or [0])] if isinstance(catalog_sections, list) else []
            max_ref = eligible[0].get("transcriptRefs", [])[-1] if eligible else segments[-1].ref
            payload["nextTranscriptRef"] = segments[next_index].ref if next_index < len(segments) and positions[segments[next_index].ref] <= positions[max_ref] else None
        return payload

    @staticmethod
    def student_view(session: DiagnosticSession) -> dict[str, Any]:
        """Serialize student-safe questions without correctness or raw response data."""
        return {
            "sessionId": session.id,
            "roomCode": session.room_code,
            "lesson": {"title": session.lesson["title"], "sourceId": session.lesson["sourceId"]},
            "status": session.status,
            "activeQuestionId": session.active_question_id,
            "activeQuestionIds": session.active_question_ids,
            "createdAt": session.created_at,
            "sections": [
                {"id": item["section"]["id"], "originalSectionId": item["section"].get("originalSectionId"), "title": item["section"]["title"], "order": item["section"]["order"], "sourceRefs": item["section"]["sourceRefs"], "concepts": item["concepts"]}
                for item in session.sections
            ],
            "questions": [
                {
                    **{key: value for key, value in item["question"].items() if key != "options"},
                    "sectionId": item["section"]["id"],
                    "options": [{key: value for key, value in option.items() if key != "correct"} for option in item["question"]["options"]],
                }
                for item in session.sections
            ],
        }
