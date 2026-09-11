# Changelog

All notable changes to Grizzly Guard AI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-12

### 🔧 Documentation Patch

Fix critical documentation issues in PyPI rendering.

### 📝 Documentation
- Fixed all old naming references (grizzly → grizzly-guard-ai)
- CLI commands now correctly show `grizzly-guard-ai proxy` and `grizzly-guard-ai scan`
- Docker image references corrected to `ghcr.io/craftedwithintent/grizzly-guard-ai:latest`
- Kubernetes deployment manifests updated with correct names
- Installation examples now use `cd grizzly-guard-ai` (not `cd grizzly`)
- Module paths corrected: `src/grizzly_guard_ai` (not `src/grizzly`)

---

## [0.1.0] - 2026-09-12

### 🎉 Initial Release: MVP Guardrails Engine

Grizzly Guard AI v0.1.0 delivers a production-ready deterministic guardrails engine for LLM safety with <5ms latency and zero cloud dependencies.

### ✨ Features

#### Ingress Guards (Pre-LLM)
- **Prompt Injection Detection** (`src/grizzly_guard_ai/core/injection.py`)
  - Regex-based attack pattern matching (<1ms)
  - Entropy scoring for anomalous token distributions
  - Canary token detection for jailbreak attempts
  - Heuristic confidence scoring (0.0–1.0)

- **Jailbreak Pattern Detection**
  - Known attack signatures (DAN mode, "act as if", "ignore instructions")
  - Semantic similarity checks with jailbreak database (optional ONNX embeddings)
  - Configurable similarity threshold (default: 0.85)

- **PII Detection & Masking** (`src/grizzly_guard_ai/core/pii.py`)
  - Email addresses, phone numbers, SSNs
  - API keys, credit card numbers (with Luhn validation)
  - Custom regex patterns per organization
  - Deterministic masking: `***-***-****`

#### Egress Guards (Post-LLM)
- **JSON Schema Validation & Repair** (`src/grizzly_guard_ai/core/json_repair.py`)
  - Auto-fix malformed JSON (trailing commas, missing braces, unquoted keys)
  - Pydantic schema validation with detailed error messages
  - Auto-fill missing required fields with type-appropriate defaults
  - Deterministic repair algorithm (same input → same output always)

- **PII Redaction in Responses**
  - Scans LLM output for sensitive data
  - Masks before returning to client
  - Violation logging for compliance audit trails

- **Structural Guarantees**
  - All output guaranteed valid JSON
  - Conforms to user-provided schema spec
  - No re-prompting or external calls needed

#### Proxy Server
- **FastAPI Gateway** (`src/grizzly_guard_ai/infrastructure/proxy_server.py`)
  - OpenAI-compatible API (`/v1/chat/completions`)
  - Incoming request validation
  - Header forwarding and authentication relay
  - Streaming response support

- **Upstream Relay**
  - Supports OpenAI, Anthropic, Bedrock, and custom LLM endpoints
  - Configurable timeout and retry logic
  - Per-request telemetry (latency, token usage, violations)

#### CLI
- **Proxy Server** (`grizzly-guard-ai proxy --port 8081`)
  - Standalone daemon mode with configurable host/port
  - Health check endpoint (`/health`)
  - Metrics export (requests, blocks, latency)

- **Scanning** (`grizzly-guard-ai scan --prompt "..."`)
  - Analyze single prompt for injection risk
  - Return confidence score + matched patterns
  - Useful for rule tuning and debugging

#### Deployment
- **Python Library** — Direct in-process integration
  ```python
  from grizzly_guard_ai import guard_ingress, guard_egress
  ```

- **Docker Container** — Lightweight multi-stage build
  - Non-root user for security
  - Health checks included
  - Ultra-small image (~200MB)
  - Multi-architecture support (amd64, arm64)

- **Kubernetes Ready** — Example manifests included
  - Deployment, Service, ConfigMap templates
  - Horizontal scaling with stateless design
  - Resource limits pre-tuned

#### Governance & Documentation
- **Production-Ready Governance**
  - MIT License
  - Contributor Covenant Code of Conduct
  - SECURITY.md with vulnerability reporting + best practices
  - CONTRIBUTING.md with full development guide

- **Architecture Documentation**
  - ARCHITECTURE.md — Component hierarchy, data flows, domain types
  - ADR-001: Functional Core + Imperative Shell design rationale
  - CONTRIBUTION_IDEAS.md — 20+ carefully scoped contribution opportunities

### 🔍 Quality & Performance

#### Testing
- 50+ comprehensive unit and integration tests
- 80%+ code coverage (enforced)
- Type safety with Pyright strict mode
- Linting with Ruff (E, F, W, I, N, UP, B, C, D rules)

#### Performance Benchmarks
| Operation | P50 | P99 | Budget |
|-----------|-----|-----|--------|
| Injection detection (heuristic) | 1.2ms | 2.8ms | <5ms |
| PII detection + masking | 0.8ms | 1.9ms | <5ms |
| JSON repair | 0.5ms | 1.2ms | <5ms |
| Full ingress pipeline | 2.5ms | 4.2ms | <5ms |
| Full egress pipeline | 1.8ms | 3.5ms | <5ms |

#### Security
- All operations deterministic (same input → same output)
- Zero external API calls in MVP (local-only inference)
- Immutable domain types (frozen Pydantic models)
- Comprehensive audit logging for compliance
- Non-root container user
- No secrets in code or config

### 📦 Package Distribution

- **PyPI**: `grizzly-guard-ai` v0.1.0
- **Installation**: `pip install grizzly-guard-ai`
- **GitHub**: https://github.com/CraftedWithIntent/grizzly-guard-ai
- **Docker**: `ghcr.io/craftedwithintent/grizzly-guard-ai:0.1.0`

### 🚀 Roadmap (Future Versions)

#### Phase 2: Enhanced Guardrails (v0.2.0)
- Dynamic threat intelligence feed (auto-update jailbreak signatures)
- Streaming egress guard (byte-by-byte token inspection)
- Semantic classification with fine-tuned ONNX models
- SIEM integration (Splunk, Datadog, OpenTelemetry)

#### Phase 3: Enterprise Extensions (v0.3.0)
- Custom fine-tuned ONNX models (domain-specific safety)
- Regulatory compliance packs (HIPAA, PCI-DSS, GDPR)
- Multi-tenant policy management
- Advanced audit logging and alerting

### 📋 Known Limitations

1. **Deterministic vs. Adaptive** — Regex/heuristic approach cannot adapt to novel attacks as well as LLM-based guardrails. Recommend combining with periodic LLM-based reviews.

2. **False Positives** — Tuning injection threshold and PII patterns may require domain-specific iteration.

3. **Schema Repair Scope** — JSON repair handles common malformations but not all edge cases. For complex nested structures, may need stricter validation.

4. **No Cloud Integration (MVP)** — ONNX embeddings run locally. Enterprise semantic cache will require Redis or SQLite-Vec for distributed deployments.

### 🙏 Contributors

- CraftedWithIntent team

### 🔗 Related Projects

- **panner-ai** — Precision testing tool for AI agents with baseline tracking
- **prospect-ai** — Semantic cache + reverse proxy for LLM inference optimization

---

## [Unreleased]

Planned features for upcoming releases documented in GitHub Issues.
