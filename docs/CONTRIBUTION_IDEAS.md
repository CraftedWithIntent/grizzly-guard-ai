# Contribution Ideas for Grizzly Guard AI

Welcome! This document outlines **20+ contribution opportunities** for Grizzly Guard AI, organized by difficulty level with impact analysis and implementation guidance.

## How to Use This Guide

1. **Pick an idea** that interests you (🟢 Easy → 🟡 Medium → 🔴 Hard)
2. **Review acceptance criteria** to understand the scope
3. **Check implementation hints** for where to start
4. **Open a GitHub issue** (we'll have pre-created ones for top 10 easy/medium ideas)
5. **Discuss in the issue** before coding (5 minutes to align)
6. **Submit a PR** (max 5 files per PR)
7. **Get feedback** and iterate

---

## 🟢 Easy Issues (Good First Contributions)

These are perfect entry points — no deep system knowledge required. Estimated effort: **0.5–2 hours**.

### 1. Add PII Detector for Credit Card Numbers

**Description:** Extend `redact_pii()` to detect and redact credit card numbers (Visa, Mastercard, Amex patterns).

**Impact/Effort Matrix:**
- 🎯 **Impact:** High (PCI compliance, common leak vector)
- ⚙️ **Effort:** 0.5 hours
- **Value:** Production systems can now mask payment data

**Acceptance Criteria:**
- [ ] New PII pattern detector in `src/grizzly/core/pii_detector.py`
- [ ] Regex patterns for Visa (16 digits), Mastercard, Amex
- [ ] Tests in `tests/test_pii_detector.py` (5+ test cases)
- [ ] Luhn algorithm validation for false positive reduction
- [ ] Config option to enable/disable credit card detection
- [ ] Example in README.md showing credit card masking
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
# In src/grizzly/core/pii_detector.py
CREDIT_CARD_PATTERNS = {
    "visa": r"\b4[0-9]{12}(?:[0-9]{3})?\b",
    "mastercard": r"\b5[1-5][0-9]{14}\b",
    "amex": r"\b3[47][0-9]{13}\b",
}

def detect_credit_card(text: str) -> List[str]:
    """Detect credit card numbers (with Luhn validation)."""
    matches = []
    for card_type, pattern in CREDIT_CARD_PATTERNS.items():
        for match in re.finditer(pattern, text):
            if luhn_check(match.group()):  # Reduce false positives
                matches.append(f"{card_type}: {match.group()}")
    return matches
```

**Why It Matters:**
- PCI DSS compliance requires masking payment data
- Credit card leaks cause regulatory fines
- Payment data is the most commonly leaked in LLM responses

---

### 2. Add Common SQL Injection Patterns to Ingress Guard

**Description:** Extend `guard_ingress()` with detection patterns for SQL injection attempts (UNION SELECT, DROP TABLE, etc.).

**Impact/Effort Matrix:**
- 🎯 **Impact:** Medium (prevents SQL injection vector)
- ⚙️ **Effort:** 1 hour
- **Value:** Agents with database access are protected

**Acceptance Criteria:**
- [ ] SQL injection patterns in `src/grizzly/core/injection_patterns.py`
- [ ] Patterns for: UNION, DROP, INSERT, DELETE, EXEC, EXECUTE, sys.
- [ ] Case-insensitive matching (with word boundaries)
- [ ] Tests in `tests/test_ingress_guard.py` (8+ test cases)
- [ ] Config option: `enable_sql_injection_check`
- [ ] Example YAML showing blocked SQL injection attempts
- [ ] Performance benchmark: <1ms for pattern matching
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
SQL_INJECTION_PATTERNS = [
    r"\b(UNION|INTERSECT|EXCEPT)\s+SELECT\b",
    r"\b(DROP|DELETE|TRUNCATE|ALTER)\s+(TABLE|DATABASE|SCHEMA)\b",
    r"\b(INSERT|UPDATE)\s+INTO\b",
    r"\b(EXEC|EXECUTE)\s*\(",
    r"sys\.(tables|columns|objects|procedures)",
    r"xp_cmdshell",
]

def check_sql_injection(prompt: str) -> Tuple[bool, str]:
    """Detect SQL injection patterns."""
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True, f"Matched pattern: {pattern}"
    return False, "No SQL injection detected"
```

**Why It Matters:**
- Agents querying databases need SQL injection protection
- Prompt injection can turn into SQL injection
- Defense in depth: multiple layers catch different attacks

---

### 3. Add JSON Schema Auto-Repair for Missing Fields

**Description:** Improve `repair_json()` to auto-populate missing required fields with default values (empty string, empty array).

**Impact/Effort Matrix:**
- 🎯 **Impact:** Medium (reduces parsing failures)
- ⚙️ **Effort:** 1 hour
- **Value:** More LLM outputs pass validation without rejection

**Acceptance Criteria:**
- [ ] Enhanced `repair_json()` in `src/grizzly/core/json_repair.py`
- [ ] Auto-fills missing required fields per schema
- [ ] Respects field type (string → "", array → [], object → {})
- [ ] Tests in `tests/test_json_repair.py` (6+ test cases)
- [ ] Handles nested objects and arrays
- [ ] Config option: `auto_fill_missing_fields`
- [ ] Example showing repair of incomplete JSON
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
def repair_json(text: str, schema: Dict) -> str:
    """Repair malformed JSON and auto-fill missing fields."""
    # Try to parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Fix common issues: trailing comma, missing quotes, etc.
    text = fix_trailing_commas(text)
    text = fix_unclosed_strings(text)
    
    parsed = json.loads(text)
    
    # Auto-fill missing required fields
    for field, field_schema in schema.get("properties", {}).items():
        if field not in parsed and field in schema.get("required", []):
            field_type = field_schema.get("type", "string")
            parsed[field] = default_for_type(field_type)
    
    return json.dumps(parsed)
```

**Why It Matters:**
- LLMs frequently omit optional fields or miss closing braces
- Rejection rate decreases → better user experience
- Production systems need robust output parsing

---

### 4. Add Request Rate Limiting to Proxy Server

**Description:** Implement per-IP rate limiting for the Grizzly Guard AI proxy (e.g., 100 req/min per IP).

**Impact/Effort Matrix:**
- 🎯 **Impact:** Medium (prevents abuse, DDoS resistance)
- ⚙️ **Effort:** 1.5 hours
- **Value:** Production deployments can control usage

**Acceptance Criteria:**
- [ ] Rate limiter in `src/grizzly/infrastructure/rate_limiter.py`
- [ ] Per-IP request counting (last 60 seconds)
- [ ] Redis backend for distributed systems (optional)
- [ ] FastAPI middleware integration
- [ ] Config: `rate_limit_requests` (default 100), `rate_limit_window_sec` (default 60)
- [ ] Returns 429 Too Many Requests when exceeded
- [ ] Tests in `tests/test_rate_limiter.py` (5+ test cases)
- [ ] Example docker-compose with Redis
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
# In src/grizzly/infrastructure/rate_limiter.py
@dataclass
class RateLimiter:
    max_requests: int = 100
    window_sec: int = 60
    
    async def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limit."""
        key = f"rate_limit:{client_ip}"
        current = await self.get_count(key)
        if current >= self.max_requests:
            return False
        await self.increment(key, expire_sec=self.window_sec)
        return True

# In proxy_server.py
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not await rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )
    return await call_next(request)
```

**Why It Matters:**
- Prevents abuse of expensive LLM API calls
- Required for multi-tenant deployments
- Standard practice for production APIs

---

## 🟡 Medium Issues (Intermediate, 2–4 hours)

Requires understanding Grizzly Guard AI internals (proxy, guards, storage).

### 5. Add Semantic Similarity Guard for Prompt Injection

**Description:** Enhance `guard_ingress()` with embeddings-based detection of novel prompt injection attacks (not in regex database).

**Impact/Effort Matrix:**
- 🎯 **Impact:** High (catches zero-day attacks)
- ⚙️ **Effort:** 2.5 hours
- **Value:** Proactive defense against emerging threats

**Acceptance Criteria:**
- [ ] Embedder integration in `src/grizzly/core/embedder.py` (ONNX FastEmbed)
- [ ] Jailbreak vector database in-memory or Redis
- [ ] `check_semantic_jailbreak()` in ingress guard
- [ ] Configurable threshold (default 0.85)
- [ ] Tests in `tests/test_semantic_guard.py` (5+ cases)
- [ ] Performance: <10ms per check
- [ ] Example: detect paraphrased jailbreak attempts
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
class SemanticGuard:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = FastEmbedding(model_name)
        self.jailbreak_db = []  # Pre-computed embeddings
    
    async def check_semantic_jailbreak(self, prompt: str, threshold=0.85):
        """Detect jailbreak via semantic similarity."""
        prompt_embedding = self.embedder.embed(prompt)
        max_similarity = 0
        most_similar = None
        
        for jailbreak_embedding, jailbreak_text in self.jailbreak_db:
            similarity = cosine_similarity(prompt_embedding, jailbreak_embedding)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = jailbreak_text
        
        return max_similarity > threshold, max_similarity, most_similar
```

**Why It Matters:**
- Regex patterns catch known attacks; embeddings catch variations
- Adversaries constantly evolve prompts to bypass detection
- Hybrid approach (regex + semantic) is industry best practice

---

### 6. Add Audit Logging with Structured JSON Output

**Description:** Implement structured audit logging that captures all guard decisions, matched patterns, and user metadata for compliance.

**Impact/Effort Matrix:**
- 🎯 **Impact:** High (compliance, debugging)
- ⚙️ **Effort:** 2 hours
- **Value:** Organizations can prove safety measures for audits

**Acceptance Criteria:**
- [ ] Audit logger in `src/grizzly/infrastructure/audit_logger.py`
- [ ] Logs ingress decisions, egress violations, PII detection
- [ ] JSON output with: timestamp, client_ip, guard_type, decision, matched_patterns
- [ ] Optional: write to file, syslog, or log aggregation service
- [ ] Config: `enable_audit_logging`, `audit_log_path`, `audit_log_level`
- [ ] Tests in `tests/test_audit_logger.py` (4+ test cases)
- [ ] Example showing compliance query (e.g., "blocked in last 24h")
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
@dataclass
class AuditEvent:
    timestamp: datetime
    client_ip: str
    user_id: Optional[str]
    guard_type: str  # "ingress" | "egress"
    decision: str  # "allow" | "block" | "warn"
    matched_patterns: List[str]
    reason: str
    original_length: int
    redacted_length: int

class AuditLogger:
    def log_ingress(self, event: AuditEvent):
        """Log ingress guard decision."""
        data = json.dumps(asdict(event), default=str)
        self.logger.info(data)
    
    def log_egress(self, event: AuditEvent):
        """Log egress guard decision."""
        data = json.dumps(asdict(event), default=str)
        self.logger.info(data)
```

**Why It Matters:**
- Regulatory compliance (HIPAA, PCI, GDPR) requires audit trails
- Debugging: understand why requests were blocked
- Threat intelligence: pattern analysis for emerging attacks

---

### 7. Add Health Check Endpoint with Guard Statistics

**Description:** Add `/health` endpoint that returns guard performance metrics (blocked/hour, PII detections, latency p99).

**Impact/Effort Matrix:**
- 🎯 **Impact:** Medium (operability, monitoring)
- ⚙️ **Effort:** 1.5 hours
- **Value:** Ops teams can monitor guard health in production

**Acceptance Criteria:**
- [ ] `/health` endpoint in proxy_server.py
- [ ] Metrics: requests_total, blocked_total, pii_violations_total, latency_p99
- [ ] Response includes: uptime, guard_version, last_updated_patterns
- [ ] Prometheus-compatible output (optional)
- [ ] Tests in `tests/test_health_check.py` (3+ cases)
- [ ] Example: K8s liveness/readiness probe configuration
- [ ] All tests pass with 80%+ coverage

**Implementation Hints:**
```python
@app.get("/health")
async def health_check():
    """Return guard health metrics."""
    return {
        "status": "healthy",
        "uptime_sec": time.time() - START_TIME,
        "metrics": {
            "requests_total": metrics.requests_total,
            "blocked_total": metrics.blocked_total,
            "pii_violations_total": metrics.pii_violations_total,
            "latency_p99_ms": metrics.get_percentile(99),
            "cache_hit_rate": metrics.cache_hit_rate,
        },
        "version": GRIZZLY_VERSION,
        "last_pattern_update": metrics.last_pattern_update,
    }
```

**Why It Matters:**
- Kubernetes + container orchestration need liveness probes
- Ops teams need visibility into guard performance
- Detecting guard degradation early prevents incidents

---

## 🔴 Hard Issues (Advanced, 4+ hours)

Requires deep knowledge of embeddings, vector DBs, or distributed systems.

### 8. Implement Distributed Cache for Jailbreak Embeddings

**Description:** Use SQLite-Vec for persistent, queryable jailbreak vector database (fast ANN search for 10k+ known attacks).

**Impact/Effort Matrix:**
- 🎯 **Impact:** High (scales to large datasets)
- ⚙️ **Effort:** 4–5 hours
- **Value:** Organizations maintain updated threat DB

**Acceptance Criteria:**
- [ ] SQLite-Vec backend in `src/grizzly/infrastructure/vector_store.py`
- [ ] Schema migrations for vectors table
- [ ] ANN search via SQLite-Vec (`SELECT * WHERE vec_distance < threshold`)
- [ ] Initial jailbreak DB (CISA, known attacks)
- [ ] Tests in `tests/test_vector_store.py` (5+ cases)
- [ ] Benchmark: <5ms search for 10k embeddings
- [ ] Docker Compose example with persistent DB
- [ ] All tests pass with 80%+ coverage

---

### 9. Add Federated Learning for Custom Guard Rules

**Description:** Allow organizations to train custom guard models on their own data without sharing prompts/responses.

**Impact/Effort Matrix:**
- 🎯 **Impact:** Very High (enterprise safety)
- ⚙️ **Effort:** 6–8 hours
- **Value:** Organizations get domain-specific guards

---

### 10. Implement Adversarial Testing Framework

**Description:** Build test suite to generate adversarial prompts and measure guard effectiveness (false positive/negative rates).

**Impact/Effort Matrix:**
- 🎯 **Impact:** High (safety validation)
- ⚙️ **Effort:** 4–6 hours
- **Value:** Prove guard effectiveness against real attacks

---

## Contribution Workflow

1. **Browse ideas above** (pick 🟢 Easy for first PR)
2. **Open a GitHub issue** linking to this doc
3. **Discuss** in the issue (5 min alignment call)
4. **Fork + branch**: `git checkout -b feat/IDEA-description`
5. **Implement** following [CONTRIBUTING.md](../CONTRIBUTING.md)
6. **Test** with 80%+ coverage
7. **Submit PR** with clear description
8. **Iterate** on feedback
9. **Celebrate** when merged! 🎉

---

## Questions?

- **GitHub Discussions:** https://github.com/CraftedWithIntent/grizzly/discussions
- **Email:** hello@craftedwithintent.ai
- **Security Concerns:** See [SECURITY.md](../SECURITY.md)

Thank you for helping make Grizzly Guard AI better! 🐻
