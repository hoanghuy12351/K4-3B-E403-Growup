"""Prompt for turning aggregate checkpoint evidence into a teacher report."""

import json
from typing import Any


PROMPT_VERSION = "class-checkpoint-assessment-v1"

SYSTEM_PROMPT = """You are a classroom decision-support assistant for VLearn.

You receive only aggregate evidence for one closed multiple-choice checkpoint.
The server has already computed counts, rates, coverage and status. Treat every
number and identifier as immutable. Produce a concise Vietnamese report for the
teacher; do not reassess individual learners.

Hard rules:
1. Never invent or alter counts, ratios, option IDs, misconception IDs or sources.
2. Use only misconception IDs present in ALLOWED_MISCONCEPTION_IDS.
3. Do not mention student names or infer individual intent, ability or reasoning.
4. computedStatus is authoritative and cannot be changed.
5. If computedStatus=insufficient_data, recommendedAction must be collect_more.
6. If computedStatus=understood, recommendedAction must be continue or clarify.
7. If computedStatus=mixed, recommendedAction must be clarify or reteach.
8. If computedStatus=needs_attention, recommendedAction must be reteach or clarify.
9. Return at most three concrete teachingMoves and keep teacherDecisionRequired=true.
10. Return only the JSON object required by the supplied schema.
"""


def build_user_prompt(metrics: dict[str, Any], computed_status: str) -> str:
    """Serialize aggregate, non-identifying evidence for the provider."""

    misconception_ids = [
        item["misconceptionId"]
        for item in metrics.get("misconceptionDistribution", [])
        if item.get("misconceptionId")
    ]
    payload = {
        "PROMPT_VERSION": PROMPT_VERSION,
        "computedStatus": computed_status,
        "ALLOWED_MISCONCEPTION_IDS": misconception_ids,
        "aggregateEvidence": metrics,
    }
    return (
        "Create a Vietnamese teacher-facing checkpoint report from this trusted "
        "aggregate evidence.\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
