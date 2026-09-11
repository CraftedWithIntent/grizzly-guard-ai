# Grizzly Architecture

## Overview

Grizzly is built on **Functional Core + Imperative Shell** (ADR-001), separating pure business logic from side effects (I/O, HTTP, CLI).

### Principles

1. **Functional Core**: Guard rules are pure functions with no side effects
2. **Imperative Shell**: Proxy server, CLI, HTTP relay, storage backends
3. **Immutability**: Pydantic frozen models ensure data integrity
4. **Determinism**: Same input → same output, no non-deterministic behavior
5. **Zero Duplication**: Single canonical model for each domain concept

---

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLI (Typer) — M1.3                                                 │
│ ├─ Parse arguments (--config, --port, --log-level)                 │
│ ├─ Initialize guard rules (prompt injection, PII, jailbreaks)      │
│ └─ Start proxy server or in-process mode                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│ Proxy Server (FastAPI) — M1.2                                       │
│ ├─ Async HTTP relay (httpx)                                        │
│ ├─ Guard ingress (catch malicious prompts)                         │
│ └─ Guard egress (mask PII, validate JSON schema)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│ Guard Pipeline (M1.0–M1.1)  [FUNCTIONAL CORE]                      │
│ ├─ guard_ingress() — Prompt injection detection + blocking         │
│ ├─ guard_egress() — PII masking + schema repair                    │
│ ├─ check_jailbreak() — Jailbreak pattern detection                 │
│ ├─ validate_schema() — JSON/XML schema conformity                  │
│ └─ redact_pii() — Email, phone, SSN, API key masking               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│ Rules Engine (M1.0–M1.1)                                           │
│ ├─ Prompt injection patterns (regex, semantic checks)              │
│ ├─ Jailbreak signatures (known attacks)                            │
│ ├─ PII patterns (email, phone, SSN, API keys)                      │
│ └─ Schema validators (JSON, XML, Pydantic)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│ Storage Backends (Future)                                          │
│ ├─ In-memory (local testing)                                       │
│ ├─ Redis (distributed, high-volume)                                │
│ └─ SQLite-Vec (persistent, semantic search)                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Ingress Guard (Prompt Injection Prevention)

**Input:** User prompt (text) + optional context

**Process:**
1. Normalize payload (trim, decode escapes)
2. Check against injection patterns:
   - Regex patterns for known attack vectors
   - Semantic similarity to jailbreak database
   - Token analysis for anomalies
3. Rate limiting + behavioral analysis (future)
4. Decision: ALLOW, BLOCK, or WARN

**Output:** `GuardDecision(status="allow" | "block" | "warn", reason, score)`

### Egress Guard (PII Masking + Schema Repair)

**Input:** LLM response (text or JSON)

**Process:**
1. Scan for PII patterns (email, phone, SSN, API keys)
2. Redact matches: `***-*-****` format
3. Parse as JSON/XML
4. Validate against schema spec
5. Repair malformed output (fix escaped quotes, add missing brackets)
6. Re-validate post-repair

**Output:** `GuardedResponse(original, redacted, repaired, violations[])`

### Proxy Relay (FastAPI Gateway)

**Input:** HTTP POST to `/v1/chat/completions` (OpenAI-compatible)

**Process:**
1. Guard ingress → validate user prompt
2. If BLOCK: return 403 + reason
3. If ALLOW: relay to upstream LLM (OpenAI, Anthropic, etc.)
4. Guard egress → mask PII, repair JSON
5. Return to client

**Output:** HTTP 200 with guarded response, or 403 if blocked

---

## Domain Types (Functional Core)

```python
# Guard rules specification
@dataclass(frozen=True)
class GuardSpec:
    ingress_checks: List[str]  # ["prompt_injection", "jailbreak"]
    egress_checks: List[str]   # ["pii_masking", "json_schema", "json_repair"]
    pii_patterns: Dict[str, str]  # Regex patterns for PII detection
    schema: Optional[Dict]  # JSON schema for output validation
    threshold: float = 0.8  # Similarity threshold for semantic matching

# Evaluation result
@dataclass(frozen=True)
class GuardDecision:
    status: Literal["allow", "block", "warn"]
    reason: str
    score: float  # 0.0 (safe) to 1.0 (threat)
    matched_patterns: List[str]

# Egress result
@dataclass(frozen=True)
class GuardedResponse:
    original: str
    redacted: str
    violations: List[str]
    repair_applied: bool
```

---

## Guard Checks (Pure Functions)

### Ingress Guards

```python
def guard_ingress(
    prompt: str, 
    rules: GuardSpec
) -> GuardDecision:
    """Detect and block prompt injection attacks."""
    # 1. Regex-based detection (fast)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt):
            return GuardDecision(
                status="block",
                reason=f"Matched pattern: {pattern}",
                score=0.95
            )
    
    # 2. Semantic similarity check (embeddings)
    embedding = embedder.embed(prompt)
    jailbreak_similarity = max(
        cosine_similarity(embedding, known_jailbreak)
        for known_jailbreak in JAILBREAK_DB
    )
    
    if jailbreak_similarity > rules.threshold:
        return GuardDecision(
            status="warn",  # or "block" if score > 0.9
            reason="High similarity to known jailbreak",
            score=jailbreak_similarity
        )
    
    return GuardDecision(
        status="allow",
        reason="Passed all ingress checks",
        score=0.0
    )

def check_jailbreak(
    prompt: str,
    rules: GuardSpec
) -> bool:
    """Detect jailbreak attack patterns."""
    # Return True if jailbreak detected
    ...
```

### Egress Guards

```python
def guard_egress(
    response: str,
    rules: GuardSpec
) -> GuardedResponse:
    """Mask PII and validate schema."""
    redacted = response
    violations = []
    
    # 1. Redact PII
    for pii_type, pattern in rules.pii_patterns.items():
        matches = re.findall(pattern, redacted)
        if matches:
            violations.append(f"Found {len(matches)} {pii_type} instances")
            redacted = re.sub(pattern, "***", redacted)
    
    # 2. Validate JSON schema
    repair_applied = False
    try:
        parsed = json.loads(redacted)
        validate(parsed, rules.schema)
    except json.JSONDecodeError:
        # Attempt repair
        redacted = repair_json(redacted)
        repair_applied = True
        parsed = json.loads(redacted)
        validate(parsed, rules.schema)
    
    return GuardedResponse(
        original=response,
        redacted=redacted,
        violations=violations,
        repair_applied=repair_applied
    )

def redact_pii(
    text: str,
    rules: GuardSpec
) -> str:
    """Redact PII patterns from text."""
    for pii_type, pattern in rules.pii_patterns.items():
        text = re.sub(pattern, f"[REDACTED {pii_type}]", text)
    return text
```

---

## Proxy Server (FastAPI)

### Request Handler

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """OpenAI-compatible chat endpoint with guardrails."""
    
    # 1. Guard ingress (validate prompt)
    user_message = request.messages[-1].content
    ingress_decision = guard_ingress(user_message, rules)
    
    if ingress_decision.status == "block":
        return ChatCompletionResponse(
            choices=[{
                "message": {"content": f"⚠️ Blocked: {ingress_decision.reason}"},
                "finish_reason": "guardrail_block"
            }]
        )
    
    # 2. Relay to upstream LLM
    response = await upstream_client.post(
        request.model_id,
        json=request.model_dump(),
        headers={"Authorization": f"Bearer {UPSTREAM_API_KEY}"}
    )
    
    # 3. Guard egress (mask PII, repair output)
    guarded = guard_egress(response.content, rules)
    
    # 4. Log violations
    if guarded.violations:
        logger.warning(f"PII detected: {guarded.violations}")
    
    return ChatCompletionResponse(
        choices=[{
            "message": {"content": guarded.redacted},
            "finish_reason": "stop"
        }],
        metadata={"guarded": True, "violations": guarded.violations}
    )
```

---

## In-Process Library

Users can also use Grizzly as a library without the proxy server:

```python
from grizzly import guard_ingress, guard_egress, GuardSpec

# Define rules
rules = GuardSpec(
    ingress_checks=["prompt_injection", "jailbreak"],
    egress_checks=["pii_masking", "json_schema"],
    pii_patterns={
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\+?1?\d{9,15}",
        "ssn": r"\d{3}-\d{2}-\d{4}"
    },
    schema={"type": "object", "properties": {"result": {"type": "string"}}}
)

# Validate ingress
user_prompt = "Tell me a secret"
decision = guard_ingress(user_prompt, rules)
if decision.status == "block":
    raise ValueError(f"Blocked: {decision.reason}")

# Validate egress
llm_response = '{"result": "user@example.com is a secret"}'
guarded = guard_egress(llm_response, rules)
print(guarded.redacted)  # Masked email
```

---

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Guard ingress (regex) | <1ms | Pattern matching only |
| Guard ingress (semantic) | 5–10ms | Embedding + similarity check |
| Guard egress (PII masking) | <2ms | Regex replacement |
| Guard egress (JSON repair) | 5–20ms | Parsing + validation |
| Proxy relay (upstream call) | 500–2,000ms | Depends on LLM provider |
| **Total (with proxy)** | **<5ms overhead** | Before relay |

---

## Error Handling

Grizzly follows fail-safe principles:

1. **Ingress guard fails → Block request** (default to safe)
2. **Egress guard fails → Return original + log violation** (never hide errors)
3. **Schema repair fails → Return as-is with violation flag** (preserve response)

---

## Related Documentation

- [ADR 001: Functional Core + Imperative Shell](adr/001-architecture.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md) — Development guide
- [SECURITY.md](../SECURITY.md) — Vulnerability reporting
