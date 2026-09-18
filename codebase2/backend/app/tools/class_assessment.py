"""Structured LLM tool for a teacher-facing aggregate checkpoint report."""

from typing import Any

from app.ai.llm.base import LLMProvider
from app.ai.llm.errors import LLMMalformedResponseError
from app.ai.llm.models import ProviderResult
from app.domain.classification import InvalidProviderOutputError
from app.prompts.class_assessment import SYSTEM_PROMPT, build_user_prompt


REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 1},
        "keyMisconceptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "interpretation": {"type": "string", "minLength": 1},
                },
                "required": ["id", "severity", "interpretation"],
                "additionalProperties": False,
            },
        },
        "recommendedAction": {
            "type": "string",
            "enum": ["continue", "clarify", "reteach", "collect_more"],
        },
        "teachingMoves": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "followUpQuestion": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "teacherDecisionRequired": {"type": "boolean"},
    },
    "required": [
        "summary", "keyMisconceptions", "recommendedAction", "teachingMoves",
        "followUpQuestion", "confidence", "limitations", "teacherDecisionRequired",
    ],
    "additionalProperties": False,
}

ALLOWED_ACTIONS = {
    "insufficient_data": {"collect_more"},
    "understood": {"continue", "clarify"},
    "mixed": {"clarify", "reteach"},
    "needs_attention": {"reteach", "clarify"},
}


class ClassAssessmentTool:
    """Call the provider, then reject claims unsupported by aggregate evidence."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate_report(self, *, metrics: dict[str, Any], computed_status: str) -> dict[str, Any]:
        result: ProviderResult = self.provider.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(metrics, computed_status),
            schema=REPORT_SCHEMA,
            request_id=f"class-assessment-{metrics['checkpointRunId']}",
        )
        if not isinstance(result.data, dict):
            raise LLMMalformedResponseError("Class-assessment provider returned invalid data.")
        return self._validate(result.data, metrics, computed_status)

    @staticmethod
    def _validate(
        payload: dict[str, Any], metrics: dict[str, Any], computed_status: str
    ) -> dict[str, Any]:
        """Validate semantic constraints not expressible in the JSON schema."""

        allowed_ids = {
            item["misconceptionId"]
            for item in metrics.get("misconceptionDistribution", [])
            if item.get("misconceptionId")
        }
        misconception_items = payload.get("keyMisconceptions")
        if not isinstance(misconception_items, list) or any(
            not isinstance(item, dict) or item.get("id") not in allowed_ids
            for item in misconception_items
        ):
            raise InvalidProviderOutputError("Provider invented a misconception ID.")
        action = payload.get("recommendedAction")
        if action not in ALLOWED_ACTIONS.get(computed_status, set()):
            raise InvalidProviderOutputError("Provider recommendation conflicts with computed status.")
        moves = payload.get("teachingMoves")
        if not isinstance(moves, list) or len(moves) > 3 or not all(isinstance(item, str) for item in moves):
            raise InvalidProviderOutputError("teachingMoves must contain at most three strings.")
        confidence = payload.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            raise InvalidProviderOutputError("confidence must be between zero and one.")
        if payload.get("teacherDecisionRequired") is not True:
            raise InvalidProviderOutputError("Teacher decision must remain required.")
        if not isinstance(payload.get("summary"), str) or not payload["summary"].strip():
            raise InvalidProviderOutputError("summary must be a non-empty string.")
        # Counts and ratios are always attached by the server. The provider only
        # explains their pedagogical meaning and cannot manufacture evidence.
        evidence_by_id = {
            item["misconceptionId"]: item
            for item in metrics.get("misconceptionDistribution", [])
            if item.get("misconceptionId")
        }
        payload["keyMisconceptions"] = [
            {
                **item,
                "count": evidence_by_id[item["id"]]["count"],
                "ratio": evidence_by_id[item["id"]]["ratio"],
                "statement": evidence_by_id[item["id"]].get("statement"),
            }
            for item in misconception_items
        ]
        return payload
