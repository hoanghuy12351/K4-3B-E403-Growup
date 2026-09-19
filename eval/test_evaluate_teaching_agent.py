from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "eval") not in sys.path:
    sys.path.insert(0, str(ROOT / "eval"))

from evaluate_teaching_agent import (  # noqa: E402
    action_matches,
    load_fixture,
    normalized_difficulty,
    question_checks,
    run_question_case,
    selected_cases,
    teacher_requested_difficulty,
)

from app.ai.config import AISettings  # noqa: E402
from app.ai.llm.models import LLMCheckpointBatchResult  # noqa: E402


def test_fixture_is_synchronized_to_twelve_cases_per_feature() -> None:
    fixture = load_fixture()
    assert fixture["counts"] == {"questionGeneration": 12, "classAnalysis": 12, "total": 24}
    assert len(fixture["questionGeneration"]) == 12
    assert len(fixture["classAnalysis"]) == 12


def test_difficulty_aliases_are_language_independent() -> None:
    assert normalized_difficulty("easy") == normalized_difficulty("dễ")
    assert normalized_difficulty("medium") == normalized_difficulty("trung bình")
    assert normalized_difficulty("hard") == normalized_difficulty("khó")


def test_difficulty_is_only_graded_when_teacher_requested_it() -> None:
    assert not teacher_requested_difficulty("Tạo 3 câu ứng dụng về temperature và top-p.")
    assert teacher_requested_difficulty("Tạo 3 câu mức trung bình.")
    assert teacher_requested_difficulty("Tạo 2 câu khó.")


def test_unspecified_difficulty_does_not_fail_question_checks() -> None:
    fixture = load_fixture()
    case = next(item for item in fixture["questionGeneration"] if item["id"] == "F1-003")
    expected = case["expectedQuestion"]
    output = {
        "interpretedRequest": {
            "questionCount": 1,
            "difficulty": None,
            "style": "tình huống",
            "focus": "token",
        },
        "questions": [{key: value for key, value in expected.items() if key not in {"answerKey", "generation"}}],
    }
    result = LLMCheckpointBatchResult.model_validate(output)
    analysis = {
        "allowedSourceRefs": expected["source"],
        "misconceptions": [
            {"id": option["misconceptionId"]}
            for option in expected["options"]
            if option["misconceptionId"]
        ],
    }
    assert question_checks(case, result, analysis)["difficulty_interpreted"] is True


def test_unsupported_file_case_passes_without_calling_generation() -> None:
    fixture = load_fixture()
    case = next(item for item in fixture["questionGeneration"] if item["id"] == "F1-011")
    settings = AISettings.from_env(ROOT / "codebase2" / "backend" / ".env")
    result = run_question_case(case, settings, None)
    assert result.passed is True
    assert result.hard_constraints_passed is True
    assert result.provider == "rules"
    assert result.output["status"] == "REJECTED_UNSUPPORTED_FILE"
    assert result.checks == {
        "unsupported_file_rejected": True,
        "generation_not_called": True,
    }


def test_action_alignment_covers_all_server_decisions() -> None:
    assert action_matches("insufficient_data", {"overview": "Chưa đủ phản hồi", "suggestedAction": "Chờ thêm phản hồi."})
    assert action_matches("continue", {"overview": "Lớp đã hiểu", "suggestedAction": "Chuyển sang phần tiếp theo."})
    assert action_matches("clarify", {"overview": "Chưa ổn định", "suggestedAction": "Làm rõ rồi hỏi lại."})
    assert action_matches("reteach", {"overview": "Còn yếu", "suggestedAction": "Giảng lại bằng phản ví dụ."})


def test_case_filter_selects_across_both_features() -> None:
    fixture = load_fixture()
    rows = selected_cases(fixture, "all", {"F1-001", "F2-005"}, None)
    assert [(feature, case["id"]) for feature, case in rows] == [
        ("question_generation", "F1-001"),
        ("class_analysis", "F2-005"),
    ]
