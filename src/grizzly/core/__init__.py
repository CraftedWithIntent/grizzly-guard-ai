"""Pure functional core guardrail validators and transformers.

No I/O side effects, no external dependencies beyond standard library.
All functions are deterministic and composable.
"""

import json
import re
import time
from typing import Any, cast

from grizzly.domain import (
    GuardResult,
    GuardStage,
    InjectionClassifierResult,
    JsonRepairResult,
    PiiClassifierResult,
    SchemaSpec,
    ViolationType,
)

# ============================================================================
# INJECTION DETECTION (Heuristic + Entropy)
# ============================================================================


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of text (0.0–1.0).

    Measures randomness. Injected prompts often have unusual entropy patterns.
    """
    if not text:
        return 0.0

    freq: dict[str, int] = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1

    entropy: float = 0.0
    text_len = len(text)
    for count in freq.values():
        prob = count / text_len
        entropy -= prob * (prob and __import__("math").log2(prob) or 0)

    # Normalize to 0.0–1.0 (max entropy for ASCII is ~4.7 bits)
    return min(entropy / 4.7, 1.0)


def detect_canary_tokens(text: str) -> list[str]:
    """Detect known canary tokens used in injection tests.

    Returns list of matched canary patterns.
    """
    canaries: list[str] = [
        r"CANARY_TOKEN",
        r"INJECTION_TEST",
        r"<INJECTION>",
        r"\[JAILBREAK\]",
    ]
    matched: list[str] = []
    for pattern in canaries:
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(pattern)
    return matched


def classify_injection_heuristic(
    prompt: str, threshold: float = 0.25
) -> InjectionClassifierResult:
    """Classify prompt for injection risk using heuristics.

    Checks:
    - Entropy anomalies
    - Known attack signatures (DAN, GPT-4 jailbreaks, etc.)
    - Canary tokens
    - Token length anomalies
    - Repetition patterns (common in injection attacks)

    Args:
        prompt: The user prompt to classify
        threshold: Risk score threshold for classification (default 0.25)

    Returns:
        Classification result with risk score (0.0–1.0).

    """
    start_time = time.perf_counter()

    detected_patterns: list[str] = []
    heuristic_flags: dict[str, Any] = {}
    risk_score: float = 0.0

    # Check entropy
    entropy = calculate_entropy(prompt)
    heuristic_flags["entropy"] = entropy
    if entropy > 0.75:
        risk_score += 0.15
        heuristic_flags["entropy_anomaly"] = True

    # Check for known jailbreak signatures
    jailbreak_patterns = [
        r"ignore previous instructions?",
        r"pretend you are",
        r"act as if",
        r"do not follow",
        r"override.*system",
        r"DAN[\s-]*mode",
        r"system prompt",
        r"assistant:\s*ignore",
        r"you are now",
    ]
    for pattern in jailbreak_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            detected_patterns.append(pattern)
            risk_score += 0.12

    # Check for canary tokens
    canaries = detect_canary_tokens(prompt)
    if canaries:
        detected_patterns.extend(canaries)
        risk_score += 0.25
        heuristic_flags["canary_tokens"] = True

    # Check token count anomaly (very short or very long)
    tokens = prompt.split()
    if len(tokens) < 3:
        heuristic_flags["token_count_low"] = True
        risk_score += 0.08
    elif len(tokens) > 2500:
        heuristic_flags["token_count_high"] = True
        risk_score += 0.15

    # Check for suspicious repetition patterns (common in injection attacks)
    # e.g., "ignore ignore ignore" or "do do do"
    words: list[str] = prompt.lower().split()
    word_counts: dict[str, int] = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    for word, count in word_counts.items():
        if len(word) > 3 and count > 2:  # Repeated word > 2 times
            risk_score += min(0.05 * count, 0.2)
            heuristic_flags["repetition_detected"] = True
            break

    # Normalize risk score to 0.0–1.0
    risk_score = min(risk_score, 1.0)
    is_injection = risk_score > threshold

    latency_ms = (time.perf_counter() - start_time) * 1000

    return InjectionClassifierResult(
        is_injection=is_injection,
        risk_score=risk_score,
        detected_patterns=detected_patterns,
        heuristic_flags=heuristic_flags,
        latency_ms=latency_ms,
    )


# ============================================================================
# PII DETECTION & MASKING
# ============================================================================


def mask_pii(text: str) -> PiiClassifierResult:
    """Detect and mask personally identifiable information.

    Patterns: SSN, email, API keys, phone numbers, credit card numbers.

    Returns masked text with PII replaced by [PII:TYPE] tokens.
    """
    start_time = time.perf_counter()

    pii_patterns: dict[str, str] = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "api_key": r"(sk_|api_|key_)[A-Za-z0-9_]{20,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    }

    masked_text = text
    detected_types: list[str] = []
    redaction_count: int = 0

    for pii_type, pattern in pii_patterns.items():
        matches = re.finditer(pattern, masked_text)
        count = 0
        for match in matches:
            masked_text = masked_text.replace(
                match.group(), f"[PII:{pii_type.upper()}]", 1
            )
            redaction_count += 1
            count += 1
        if count > 0:
            detected_types.append(pii_type)

    latency_ms = (time.perf_counter() - start_time) * 1000

    return PiiClassifierResult(
        pii_found=len(detected_types) > 0,
        detected_types=detected_types,
        masked_text=masked_text,
        redaction_count=redaction_count,
        latency_ms=latency_ms,
    )


# ============================================================================
# JSON REPAIR & SCHEMA VALIDATION
# ============================================================================


def repair_json(text: str) -> JsonRepairResult:
    """Attempt deterministic repair of malformed JSON.

    Fixes:
    - Missing closing braces/brackets
    - Unquoted string keys
    - Trailing commas
    - Single quotes → double quotes

    Returns repaired JSON string (valid JSON if successful).
    """
    mutations: list[str] = []
    repaired = text

    # Try parsing first
    try:
        json.loads(repaired)
        return JsonRepairResult(
            original=text,
            repaired=repaired,
            valid=True,
            mutations=[],
        )
    except json.JSONDecodeError:
        pass

    # Attempt repairs
    # 1. Fix trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    mutations.append("removed_trailing_commas")

    # 2. Replace single quotes with double quotes (naive approach)
    # Only if it doesn't break apostrophes in words
    if repaired.count("'") > repaired.count('"'):
        repaired = repaired.replace("'", '"')
        mutations.append("replaced_single_quotes")

    # 3. Add missing closing braces/brackets
    open_braces = repaired.count("{") - repaired.count("}")
    if open_braces > 0:
        repaired += "}" * open_braces
        mutations.append(f"added_{open_braces}_closing_braces")

    open_brackets = repaired.count("[") - repaired.count("]")
    if open_brackets > 0:
        repaired += "]" * open_brackets
        mutations.append(f"added_{open_brackets}_closing_brackets")

    # 4. Try parsing repaired version
    valid = False
    try:
        json.loads(repaired)
        valid = True
    except json.JSONDecodeError:
        pass

    return JsonRepairResult(
        original=text,
        repaired=repaired,
        valid=valid,
        mutations=mutations,
    )


def validate_json_schema(data: Any, schema: SchemaSpec) -> bool:
    """Validate JSON data against schema.

    Basic validation: check required fields and type conformance.

    For MVP, simple checks. Phase 2 can use jsonschema library.
    """
    if not isinstance(data, dict):
        return False

    # Check required fields
    for field in schema.required_fields:
        if field not in data:
            return False

    # Check strict mode (no unknown fields)
    if not schema.strict:
        return True

    # Get allowed field names from schema
    allowed_fields = set(schema.required_fields)
    schema_props = schema.json_schema.get("properties", {})
    if isinstance(schema_props, dict):
        for prop_name in cast(dict[str, Any], schema_props):
            allowed_fields.add(str(prop_name))

    # Check all data keys are allowed
    for data_key in cast(dict[str, Any], data):
        if str(data_key) not in allowed_fields:
            return False

    return True


# ============================================================================
# INGRESS & EGRESS PIPELINE
# ============================================================================


def guard_ingress(
    prompt: str,
    injection_threshold: float = 0.25,
    mask_pii_flag: bool = True,
) -> GuardResult:
    """Pre-LLM ingress validation pipeline.

    Steps:
    1. Classify for injection risk
    2. Optionally mask PII
    3. Return decision (passed/blocked)

    Args:
        prompt: User input prompt
        injection_threshold: Risk score threshold (default 0.25)
        mask_pii_flag: Whether to mask PII (default True)

    Returns:
        GuardResult with violations list.

    """
    start_time = time.perf_counter()
    violations: list[ViolationType] = []
    masked_payload = prompt

    # Step 1: Injection classification
    injection_result = classify_injection_heuristic(prompt, threshold=injection_threshold)
    if injection_result.is_injection:
        violations.append(ViolationType.PROMPT_INJECTION)

    # Step 2: Optional PII masking
    if mask_pii_flag:
        pii_result = mask_pii(prompt)
        if pii_result.pii_found:
            violations.append(ViolationType.PII_DETECTED)
            masked_payload = pii_result.masked_text

    latency_ms = (time.perf_counter() - start_time) * 1000

    return GuardResult(
        passed=len(violations) == 0,
        stage=GuardStage.INGRESS,
        violations=violations,
        confidence=injection_result.risk_score,
        masked_payload=masked_payload,
        original_payload=prompt,
        latency_ms=latency_ms,
        metadata={
            "injection_risk": injection_result.risk_score,
            "detected_patterns": injection_result.detected_patterns,
            "pii_redacted": len(violations) > 0 and ViolationType.PII_DETECTED in violations,
        },
    )


def guard_egress(
    llm_output: str,
    schema: SchemaSpec | None = None,
    mask_pii_flag: bool = True,
) -> GuardResult:
    """Post-LLM egress validation & repair pipeline.

    Steps:
    1. Attempt to parse JSON
    2. Repair if malformed
    3. Validate against schema
    4. Optionally mask PII
    5. Return result
    """
    start_time = time.perf_counter()
    violations: list[ViolationType] = []
    masked_payload = llm_output

    # Step 1–2: JSON repair
    repair_result = repair_json(llm_output)
    if not repair_result.valid:
        violations.append(ViolationType.MALFORMED_JSON)

    # Step 3: Schema validation (if provided)
    if schema is not None:
        try:
            parsed = json.loads(repair_result.repaired)
            if not validate_json_schema(parsed, schema):
                violations.append(ViolationType.SCHEMA_MISMATCH)
        except json.JSONDecodeError:
            violations.append(ViolationType.MALFORMED_JSON)

    # Step 4: Optional PII masking
    if mask_pii_flag:
        pii_result = mask_pii(repair_result.repaired)
        if pii_result.pii_found:
            violations.append(ViolationType.PII_DETECTED)
            masked_payload = pii_result.masked_text
        else:
            masked_payload = repair_result.repaired
    else:
        masked_payload = repair_result.repaired

    latency_ms = (time.perf_counter() - start_time) * 1000

    return GuardResult(
        passed=len(violations) == 0,
        stage=GuardStage.EGRESS,
        violations=violations,
        confidence=1.0 if repair_result.valid else 0.5,
        masked_payload=masked_payload,
        original_payload=llm_output,
        latency_ms=latency_ms,
        metadata={
            "json_valid": repair_result.valid,
            "mutations": repair_result.mutations,
            "schema_checked": schema is not None,
        },
    )
