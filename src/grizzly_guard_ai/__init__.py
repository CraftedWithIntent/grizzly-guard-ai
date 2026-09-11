"""Grizzly: Deterministic LLM Guardrails Engine.

Sub-5ms deterministic screening for prompt injection, PII masking, and JSON
schema enforcement. Runs locally, no cloud dependencies.

Example usage:
    from grizzly import guard_ingress, guard_egress

    # Pre-LLM validation
    result = guard_ingress("User prompt here")
    if not result.passed:
        print(f"Blocked: {result.violations}")

    # Post-LLM validation
    result = guard_egress('{"output": "LLM response"}')
    print(f"Safe output: {result.masked_payload}")
"""

from grizzly_guard_ai.core import (
    classify_injection_heuristic,
    guard_egress,
    guard_ingress,
    mask_pii,
    repair_json,
    validate_json_schema,
)
from grizzly_guard_ai.domain import (
    GuardResult,
    GuardStage,
    InjectionClassifierResult,
    JsonRepairResult,
    MaskedPayload,
    PiiClassifierResult,
    SchemaSpec,
    ViolationType,
)

__version__ = "0.1.0-dev"

__all__ = [
    "guard_ingress",
    "guard_egress",
    "classify_injection_heuristic",
    "mask_pii",
    "repair_json",
    "validate_json_schema",
    "GuardResult",
    "GuardStage",
    "ViolationType",
    "InjectionClassifierResult",
    "JsonRepairResult",
    "MaskedPayload",
    "PiiClassifierResult",
    "SchemaSpec",
]
