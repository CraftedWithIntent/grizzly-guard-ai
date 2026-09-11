"""Domain types for Grizzly guardrails engine.

Immutable, serializable data structures representing guardrail decisions,
violations, and masked payloads. Pure data, no I/O side effects.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any


class ViolationType(StrEnum):
    """Classification of guardrail violations."""

    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    PII_DETECTED = "pii_detected"
    MALFORMED_JSON = "malformed_json"
    SCHEMA_MISMATCH = "schema_mismatch"
    TOXIC_CONTENT = "toxic_content"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    ENTROPY_ANOMALY = "entropy_anomaly"


class GuardStage(StrEnum):
    """Execution stage: ingress (pre-LLM) or egress (post-LLM)."""

    INGRESS = "ingress"
    EGRESS = "egress"


@dataclass(frozen=True)
class GuardResult:
    """Immutable decision result from a guardrail check.

    Attributes:
        passed: True if guardrail check passed (no violations)
        stage: INGRESS (pre-LLM) or EGRESS (post-LLM)
        violations: List of detected violation types (empty if passed)
        confidence: Confidence score (0.0–1.0) for violation detection
        masked_payload: Masked/sanitized version of input (if mutations applied)
        original_payload: Original input payload
        latency_ms: Execution time in milliseconds
        metadata: Additional context (reason, matched_pattern, etc.)

    """

    passed: bool
    stage: GuardStage
    violations: list[ViolationType]
    confidence: float
    masked_payload: str
    original_payload: str
    latency_ms: float
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = "confidence must be between 0.0 and 1.0"
            raise ValueError(msg)
        if self.latency_ms < 0:
            msg = "latency_ms must be non-negative"
            raise ValueError(msg)


@dataclass(frozen=True)
class MaskedPayload:
    """Result of masking operation (PII, secrets, etc.).

    Attributes:
        original: Unmasked input
        masked: Masked output
        redactions: List of redaction metadata (type, count, example)

    """

    original: str
    masked: str
    redactions: list[dict[str, Any]]


@dataclass(frozen=True)
class JsonRepairResult:
    """Result of deterministic JSON repair operation.

    Attributes:
        original: Original (potentially malformed) JSON string
        repaired: Repaired JSON string (valid JSON)
        valid: True if original was already valid JSON
        mutations: List of applied repairs (corrected quotes, trailing commas, etc.)

    """

    original: str
    repaired: str
    valid: bool
    mutations: list[str]


@dataclass(frozen=True)
class SchemaSpec:
    """JSON schema specification for validation/repair.

    Attributes:
        name: Schema identifier
        json_schema: Full JSON schema dict (JSON Schema draft 7+)
        required_fields: List of required field names
        strict: Enforce strict validation (fail on unknown fields)

    """

    name: str
    json_schema: dict[str, Any]
    required_fields: list[str]
    strict: bool


@dataclass(frozen=True)
class InjectionClassifierResult:
    """Result of prompt injection classification.

    Attributes:
        is_injection: True if prompt appears to be injection attempt
        risk_score: Confidence score (0.0–1.0)
        detected_patterns: List of matched attack signatures
        heuristic_flags: Dict of heuristic checks (entropy, canaries, etc.)
        latency_ms: Execution time

    """

    is_injection: bool
    risk_score: float
    detected_patterns: list[str]
    heuristic_flags: dict[str, Any]
    latency_ms: float


@dataclass(frozen=True)
class PiiClassifierResult:
    """Result of PII detection and masking.

    Attributes:
        pii_found: True if PII detected
        detected_types: List of PII types (ssn, email, api_key, etc.)
        masked_text: Text with PII redacted
        redaction_count: Number of redactions applied
        latency_ms: Execution time

    """

    pii_found: bool
    detected_types: list[str]
    masked_text: str
    redaction_count: int
    latency_ms: float
