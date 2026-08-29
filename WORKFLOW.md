# WORKFLOW.md - How to Prompt Ash for Work on Grizzly

This document defines how to direct work on Grizzly (deterministic LLM guardrails engine) and what to expect from execution.

**tl;dr:** Specify project context (implicit or explicit) → pick an issue → I handle the rest (branch → code → test → PR → review).

---

## Project Context: Grizzly

**Workspace:** `/Users/philipthomas/.openclaw/workspaces/grizzly`  
**Repository:** `https://github.com/CraftedWithIntent/grizzly`  
**Tech Stack:** Python 3.11+, FastAPI, Pydantic, uv, pytest  
**Scope:** MVP phase 1 (deterministic guardrails, 3–4 weeks solo coding)

Grizzly is **totally independent** of Assay, Crucible, flow-ledger, game-dev, and orchestrators. It has its own GitHub repo, CI/CD, and domain logic.

---

## Directing Work on Grizzly

### Standard Prompt (Explicit Project)

```
Work on grizzly M1.1

or

Start grizzly issue #5

or

Finish grizzly M1.3 and close it
```

### Standard Prompt (Implicit, When in Grizzly Session)

```
Work on M1.1

or

Start issue #3
```

(Assumes current session is Grizzly; I resolve to grizzly workspace automatically)

**What I do:**
1. Route to `/Users/philipthomas/.openclaw/workspaces/grizzly/`
2. Read issue fully (title, body, acceptance criteria, labels)
3. Check for blockers (open PRs, broken main, upstream dependencies)
4. Create feature branch: `feature/M1.{Y}-{description}`
5. Execute work (code + tests per Phase 1 scope)
6. Create PR with semantic commit message
7. Update issue label: `status:backlog` → `status:in-progress` → `status:review`
8. Wait for your approval/merge

---

## Grizzly-Specific Execution Discipline

### Pre-Work Checklist (MANDATORY)

Before I write any code on Grizzly:

1. ✅ **Navigate to Grizzly workspace** — `cd ~/.openclaw/workspaces/grizzly/`
2. ✅ **Check for open PRs** — `gh pr list --state open` must be empty
3. ✅ **Verify main branch clean** — No pending merges or conflicts
4. ✅ **Codebase Reconnaissance** — Search for existing:
   - Domain types (GuardResult, ViolationType, etc.)
   - Core logic (injection detection, PII masking, JSON repair)
   - Infrastructure stubs (proxy server, ONNX runtime, etc.)
5. ✅ **Run local validation suite**:
   ```bash
   uv pip install -e ".[dev]"
   ruff check src tests
   pyright src
   pytest tests --cov=src/grizzly
   python -m build
   ```
   All must pass (0 errors, 0 warnings).
6. ✅ **Update issue label** — `status:backlog` → `status:in-progress`
7. ✅ **Create feature branch** — `git checkout -b feature/M1.{Y}-{description}`
8. ✅ Only THEN start coding

### Branch Strategy

```
main (production-ready, always green)
  ↑
feature/M1.1-ingress-guards
  ↑
(local development)
  ↓
PR #N (code review)
  ↓
Merged to main via squash/rebase
```

Never commit directly to main. All work is feature-branch + PR.

### Code Quality Gates

**Linting:**
```bash
ruff check src tests
```
Must pass with 0 violations.

**Type Checking:**
```bash
pyright src
```
Strict mode, 0 errors.

**Tests:**
```bash
pytest tests --cov=src/grizzly
```
- All tests passing
- Coverage ≥ 80%
- Test structure: `test_functional_core.py`, `test_injection_fuzzing.py`, `test_latency_benchmarks.py`

**Build:**
```bash
python -m build
```
Produces clean wheel + sdist.

### Commit Discipline

```
feat(core): implement heuristic injection detector
fix(pii): handle apostrophes in PII masking
docs(readme): add configuration guide
test(egress): add schema validation tests
```

One logical change per commit. Semantic messages per Conventional Commits.

### PR Requirements

**Title Format:**
```
M1.1: Heuristic Injection Detection & Entropy Scoring
```

**Body Template:**
```
## Description
Implements heuristic-based prompt injection detection (regex + entropy + canary tokens).

## Changes
- Added core/injection.py (classification logic)
- Added domain/types.py (InjectionClassifierResult)
- Updated test_functional_core.py with injection tests

## Testing
- test_functional_core.py: Benign, jailbreak, entropy, canary token tests
- Latency benchmark: <5ms P50, <3ms P99 on heuristic classification
- Coverage: 95%

## Related Issue
Closes #1

## Notes
Heuristic-only MVP (no ONNX model in Phase 1). ONNX classifier deferred to Phase 2.
```

---

## Grizzly Phase 1 Issue Breakdown

### M1.1: Heuristic Injection Detection & Entropy Scoring
- Regex signature matching (known jailbreaks: DAN, GPT-4, etc.)
- Shannon entropy calculation (detect anomalous text)
- Canary token detection (INJECTION_TEST, etc.)
- Configurable risk threshold
- **Files:** `src/grizzly/core/__init__.py` (injection.py section)
- **Tests:** `tests/test_functional_core.py` (injection tests)

### M1.2: PII Detection & Masking
- Detect: SSN, email, API keys, phone numbers, credit card numbers
- Mask: Replace with [PII:TYPE] tokens
- Preserve masked text for downstream processing
- **Files:** `src/grizzly/core/__init__.py` (pii.py section)
- **Tests:** `tests/test_functional_core.py` (PII tests)

### M1.3: Deterministic JSON Repair & Schema Validation
- Fix malformed JSON (trailing commas, unclosed braces, unquoted keys)
- Validate against JSON Schema
- Never re-prompt LLM (pure algorithmic)
- **Files:** `src/grizzly/core/__init__.py` (grammar.py section)
- **Tests:** `tests/test_functional_core.py` (JSON repair tests)

### M1.4: Ingress Guard Pipeline (Pre-LLM)
- Compose injection detection + PII masking + token length checks
- Return GuardResult with violations & sanitized payload
- Latency budget: <5ms
- **Files:** `src/grizzly/core/__init__.py` (guard_ingress function)
- **Tests:** `tests/test_functional_core.py` (ingress tests)

### M1.5: Egress Guard Pipeline (Post-LLM)
- Compose JSON repair + schema validation + PII masking
- Return GuardResult with sanitized output
- Latency budget: <5ms
- **Files:** `src/grizzly/core/__init__.py` (guard_egress function)
- **Tests:** `tests/test_functional_core.py` (egress tests)

### M1.6: Proxy Server (FastAPI)
- HTTP server listening on localhost:8081
- Accept LLM requests (forward to upstream provider)
- Apply ingress/egress guards transparently
- **Files:** `src/grizzly/infrastructure/proxy_server.py`
- **Tests:** `test_proxy_streaming.py` (streaming, error handling)

### M1.7: CLI & Health Check
- `grizzly proxy --port 8081` command
- `grizzly scan --prompt "..."` command
- `/health` endpoint (liveness probe)
- **Files:** `src/grizzly/cli.py`, infrastructure updates
- **Tests:** CLI tests, integration tests

### M1.8: Docker & Deployment Artifacts
- Multi-stage Dockerfile (<200MB image)
- GitHub Action for PyPI + GHCR publish
- Kubernetes starter manifests
- **Files:** `Dockerfile`, `.github/workflows/publish.yml`
- **Tests:** Build verification, image size check

---

## Expected Outcomes Per Issue

### Features (M1.1–M1.7)

**You'll get:**
- Feature branch with passing tests
- PR with implementation + tests + updated architecture docs
- Clean git history (rebase, no merge commits)
- Exit criteria met (acceptance criteria from issue checked off)

**Success Criteria:**
- All tests passing (`pytest --cov=src/grizzly`)
- Ruff + pyright clean (0 violations)
- Latency benchmark met (e.g., <5ms on guard operations)
- Code merged to main

### Deployment (M1.8)

**You'll get:**
- Docker image built and pushed to GHCR
- PyPI package published
- GitHub release with binary artifacts
- CI workflow green on all Python versions (3.11, 3.12)

---

## Communication & Progress Updates

### During Work

If I finish in one session:
```
✅ grizzly M1.1 complete. PR ready: #2
Status: Heuristic injection detection + entropy scoring done.
Latency benchmark: 2.1ms P50, 3.8ms P99 on benign prompt.
Tests: 12 test cases, 100% coverage.
```

If work spans multiple sessions:
```
🌿 Working on grizzly M1.3 (JSON Repair).
Status: Trailing comma removal 100%, unclosed brace handling 60%.
Blocker: None.
ETA: Next session (2 hours more).
```

### If I Hit a Blocker

Example: ONNX model compatibility issue (deferred to Phase 2).

```
🚫 BLOCKED: grizzly M1.6 (Proxy Server)
Reason: FastAPI streaming + SSE chunk reconstruction is complex; Phase 1 should be simpler
Options:
  A) Implement basic proxy without streaming (Phase 1)
  B) Defer proxy to Phase 1+ and focus on library first
Recommendation: Option A (library first, proxy Phase 1+)
Awaiting: Your direction
```

### When Done

```
✅ grizzly M1.X merged to main. Branch deleted.
Ready for grizzly M1.Y or any other project.
```

---

## Approval & Review Expectations

### PR Review Workflow

1. I create PR → `status:review`
2. You review (or auto-approve if aligned)
3. If approved:
   - I merge (squash/rebase, no merge commits)
   - Delete feature branch
   - Close issue (auto-linked in PR)
4. If revisions needed:
   - You leave comments
   - I update branch with new commits
   - Ready for re-review

### Automated Checks (No Manual Approval Needed)

- Ruff linting (enforced via pre-commit)
- Pyright type checking (enforced in CI)
- Test coverage (≥ 80% gated by pytest)
- Build artifact generation

**You approve for:**
- Architecture alignment (guard design, pipeline composition)
- Feature completeness (acceptance criteria met)
- Latency benchmarks (<5ms gates enforced)
- Docs quality (README, WORKFLOW updates)

---

## Escalation & Decisions

If I encounter ambiguity mid-task:

```
❓ grizzly M1.2 (PII Masking): Should we support masking for masked credit card (last 4 digits)?
Options:
  A) Mask all credit cards (strict)
  B) Keep last 4 digits visible (usability)
  C) Configurable (best flexibility)
Recommendation: Option C (align with Phase 2 enterprise compliance)
Awaiting: Your call
```

I'll propose and wait for your decision. Never assume design on Grizzly.

---

## Examples: Full Work Cycles

### Example 1: Simple Feature (M1.1 — Injection Detection)

```
You: Work on grizzly M1.1

Me:
✓ Routing: ~/.openclaw/workspaces/grizzly/
✓ Pre-work checklist passed (main clean, no open PRs)
✓ Branch created: feature/M1.1-injection-detection
✓ Code written: src/grizzly/core/__init__.py (injection detection)
✓ Tests added: tests/test_functional_core.py (12 test cases, 100% coverage)
✓ Build passing: ruff ✓ | pyright ✓ | pytest ✓
✓ PR created: #2 "M1.1: Heuristic Injection Detection & Entropy Scoring"
```

You review → approve → I merge → Issue #1 closes automatically.

---

### Example 2: Performance-Critical Issue (M1.4 — Ingress Pipeline)

```
You: Finish grizzly M1.4 with <5ms latency guarantee

Me:
✓ Pre-work checklist passed
✓ Branch created: feature/M1.4-ingress-pipeline
✓ Ingress guard implemented: injection + PII + token checks
✓ Latency benchmarks: 2.5ms P50, 4.2ms P99 (well under budget)
✓ Test suite: 8 test cases, coverage 92%
✓ PR #4 includes latency profiles + benchmark results
```

You approve latency targets → I merge → Issue closes.

---

## Workflow Summary

| Step | Owner | Input | Output |
|------|-------|-------|--------|
| 1. Route Project | Me | Project name (grizzly) | Workspace path resolved |
| 2. Pick Issue | You | Issue number (M1.X or #Y) | "Got it, starting work" |
| 3. Pre-Check | Me | Issue details + workspace validation | Blockers identified or clear |
| 4. Code & Test | Me | Acceptance criteria | Feature branch with tests |
| 5. PR | Me | Code + tests | PR #N ready for review |
| 6. Review | You | PR changes | Approved or revision requests |
| 7. Merge | Me | Approval | Main updated, issue closed |
| 8. Report | Me | Completion | Ready for next issue |

---

## Grizzly-Specific Notes

- **Sub-5ms Latency:** Strict performance budget across all guard operations. No exceptions.
- **Heuristic-First MVP:** No ONNX model in Phase 1. Regex + entropy + pattern matching only.
- **Local-Only:** Zero cloud dependencies. All inference runs on local CPU.
- **Deterministic:** Same input → same output, always. No non-determinism.
- **No Monetization in Repo:** Cloud threat feeds and enterprise compliance packs are separate SaaS products, not in open-source code.

---

## Questions?

If you're unsure how to direct work on Grizzly, default to:

```
Work on grizzly M1.X
```

I'll handle the rest. This document is your reference for what happens behind the scenes.

---

**Ash, Primary Orchestrator**  
Grizzly Project (v0.1.0-dev) — Independent Workspace  
Last Updated: 2026-08-30
