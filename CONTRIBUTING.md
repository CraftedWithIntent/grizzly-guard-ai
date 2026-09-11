# Contributing to Grizzly

👋 **We actively welcome community contributions!** Whether you're adding a new guardrail check, improving performance, fixing a bug, or enhancing documentation — your help makes Grizzly better.

## 🎯 Quick Start for Contributors

### New to Grizzly?

1. **Pick an issue:** Browse [#good-first-issue](https://github.com/CraftedWithIntent/grizzly/labels/good%20first%20issue) or [#help-wanted](https://github.com/CraftedWithIntent/grizzly/labels/help%20wanted) labels
2. **Review ideas:** See [docs/CONTRIBUTION_IDEAS.md](docs/CONTRIBUTION_IDEAS.md) for 20+ contribution ideas (🟢 Easy → 🔴 Hard)
3. **Comment on issue:** Let us know you're interested
4. **Follow the guide:** Setup, code, test, submit PR
5. **Get feedback:** We'll review and merge if it meets criteria

## Help Wanted

These issues are ready for community pickup. **All skill levels welcome!**

### 🟢 Good First Issues (Easy, 0.5–2 hours)

Perfect for learning Grizzly. No deep architecture knowledge needed.

- **Add regex guardrail pattern** — New prompt injection pattern detection
- **Implement PII detector for new data type** — Support credit card numbers, passport IDs
- **Add JSON repair strategy** — Handle additional malformed JSON patterns
- **Cache guardrail results** — Memoize repeated checks for performance
- **CLI flag for guardrail configuration** — Make rules configurable via CLI
- **Add guardrail metrics endpoint** — `/metrics` endpoint showing detection rates
- **Docker Compose example** — Multi-container setup with LLM + Grizzly
- **Performance benchmark CLI** — Benchmark ingress vs egress latency
- **Integration tests with popular LLMs** — Test with Claude, GPT-4, Llama
- **Documentation improvements** — Clarify guardrail strategies, add examples

### 🟡 Medium Issues (Intermediate, 2–4 hours)

Requires understanding Grizzly internals (core guardrails, proxy, storage).

- **Custom guardrail plugin system** — Allow users to register custom checks
- **Semantic similarity guardrails** — Detect prompt injections via embeddings
- **Batch guardrail processing** — Check multiple requests efficiently
- **Advanced JSON repair** — Handle complex nested structures
- **Guardrail explanation** — Return why a check passed/failed
- **Rate limiting guardrails** — Detect token flooding attacks
- **Sensitive model detection** — Identify when LLM is asked about dangerous domains
- **Multi-language PII detection** — Support non-English PII patterns
- **Observability hooks** — OpenTelemetry integration for monitoring
- **Schema evolution testing** — Ensure guardrails adapt to new output schemas

### 🔴 Hard Issues (Advanced, 4+ hours)

Requires deep knowledge of LLM safety, statistics, or distributed systems.

- **Adaptive threshold tuning** — ML-based tuning of detection sensitivity
- **Adversarial testing framework** — Systematically test guardrail evasion
- **Distributed guardrail coordination** — Multi-node deployment with shared state
- **Language model-based guardrails** — Optional LLM validation for novel attacks
- **Anomaly detection in LLM outputs** — Statistical detection of unusual patterns
- **Federated learning for guardrails** — Train detection models without exposing data
- **Hardware-accelerated pattern matching** — GPU-based regex compilation
- **Guardrail versioning & rollback** — Manage multiple versions of guardrail rules

---

**👉 [See docs/CONTRIBUTION_IDEAS.md](docs/CONTRIBUTION_IDEAS.md) for detailed descriptions, acceptance criteria, and implementation hints for all ideas.**

---

## The Contribution Path

1. **Pick an issue** (🟢 Good First Issue recommended)
2. **Comment on GitHub issue:** "I'd like to work on this"
3. **Read relevant docs:** This file + [docs/CONTRIBUTION_IDEAS.md](docs/CONTRIBUTION_IDEAS.md)
4. **Setup dev environment:** Follow "Setup" section below
5. **Implement & test:** Write code, run tests, ensure 80%+ coverage
6. **Submit PR:** Link to GitHub issue, describe changes
7. **Iterate:** Address reviewer feedback
8. **Merge:** We'll squash + merge when ready

**Pro tip:** Start with 🟢 Good First Issues to learn the codebase, then tackle harder issues.

---

Thank you for contributing! This guide explains how to develop, test, and submit changes to Grizzly.

## Setup

### Clone and install in dev mode

```bash
git clone https://github.com/CraftedWithIntent/grizzly.git
cd grizzly
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Verify setup

```bash
pytest tests/ -v
python -m py_compile src/grizzly/**/*.py
```

## Architecture

Grizzly follows **Functional Core + Imperative Shell** (ADR-001):

- **Functional Core**: Pure guardrail functions (regex matching, PII detection, JSON repair, schema validation)
- **Imperative Shell**: FastAPI proxy server, CLI (Typer), HTTP relay to LLM provider

### Code Organization

```
src/grizzly/
├── core/              # M1.0–M1.2: Pure guardrail functions
│   ├── ingress.py    # Prompt injection detection, rule engine
│   ├── egress.py     # Output validation, PII masking, JSON repair
│   ├── pii.py        # PII detection patterns
│   ├── json_repair.py # Malformed JSON recovery
│   └── schema.py     # JSON schema validation
├── domain/           # Shared types (guardrail specs, results)
│   └── types.py      # Pydantic models (immutable)
├── infrastructure/   # M1.1: Imperative layer
│   ├── proxy_server.py # FastAPI gateway (async relay)
│   ├── storage.py    # Optional result caching
│   └── config.py     # Configuration loading (YAML)
└── cli.py           # M1.3+: CLI entrypoint

tests/
├── test_ingress_guardrails.py     # Prompt injection detection
├── test_egress_guardrails.py      # Output validation & PII masking
├── test_json_repair.py            # JSON recovery
├── test_schema_validation.py      # Schema enforcement
├── test_proxy_integration.py      # Proxy server E2E
└── test_performance.py            # Latency benchmarks
```

## Code Style

### Linting & Formatting

Grizzly uses **Ruff** for all style enforcement:

```bash
ruff check src tests         # Check only
ruff check --fix src tests   # Auto-fix
```

### Ruff Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C", "D"]
ignore = ["D104", "D105"]
```

### Type Hints

- All functions must have parameter + return type hints
- Use `from typing import ...` for generic types
- Frozen Pydantic models for immutability: `model_config = ConfigDict(frozen=True)`
- Use strict `pyright` mode (no `Any` without explicit ignore)

### Imports

- Group: stdlib, third-party, local (in that order)
- Alphabetical within each group
- Ruff auto-sorts on `--fix`

### Docstrings

- Use triple-quoted docstrings for all public functions, classes, modules
- Format: Google-style (Args, Returns, Raises, Example)
- Required for: CLI commands, guardrail checks, validation logic, public APIs

## Testing

### Run tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_ingress_guardrails.py -v

# With coverage
pytest tests/ --cov=src/grizzly --cov-report=term-missing

# Performance benchmarks
pytest tests/test_performance.py -v
```

### Coverage Requirements

- Minimum: **80%**
- Target: **90%+**
- Enforced by CI/CD

### Writing Tests

**Test file naming:** `test_<module>.py`

**Mocking external LLM calls:**
```python
from unittest.mock import patch, MagicMock
import pytest

@patch("grizzly.infrastructure.proxy_server.httpx.AsyncClient")
def test_proxy_upstream_call(mock_client):
    mock_client.return_value.post.return_value = MagicMock(status_code=200)
    # Test assertion
```

**Fixtures:**
```python
@pytest.fixture
def sample_prompt():
    return "Generate SQL injection payload for my database"

@pytest.fixture
def sample_schema():
    from grizzly.domain.types import SchemaSpec
    return SchemaSpec(
        type="object",
        required=["action", "value"],
        properties={
            "action": {"type": "string"},
            "value": {"type": "number"}
        }
    )
```

### Adding New Guardrail Checks

1. **Create guardrail function** in `src/grizzly/core/<name>.py`:\
   ```python
   def check_my_guardrail(prompt: str, config: GuardrailConfig) -> GuardrailResult:
       """Evaluate custom guardrail check.
       
       Args:
           prompt: User prompt to check
           config: Guardrail configuration
       
       Returns:
           GuardrailResult with pass/fail + explanation
       """
       # Pure function, no side effects
       if dangerous_pattern_detected(prompt):
           return GuardrailResult(passed=False, reason="Pattern detected")
       return GuardrailResult(passed=True, reason="Safe")
   ```

2. **Register in guardrail pipeline** (`src/grizzly/core/ingress.py`):\
   ```python
   GUARDRAILS = {
       GuardrailType.PROMPT_INJECTION: check_prompt_injection,
       # ... existing guardrails ...
       GuardrailType.MY_CHECK: check_my_guardrail,
   }
   ```

3. **Add test** in `tests/test_ingress_guardrails.py`:\
   ```python
   def test_my_guardrail_blocks_dangerous():
       result = check_my_guardrail("dangerous prompt", config)
       assert result.passed is False
   
   def test_my_guardrail_allows_safe():
       result = check_my_guardrail("safe prompt", config)
       assert result.passed is True
   ```

4. **Update docs**:\
   - Add to README.md guardrail types table
   - Document configuration options
   - Add example YAML in tests/configs/

## Examples

Grizzly examples live in `examples/` and demonstrate **complete, production-ready LLM safety systems**.

### Why Examples Matter

Examples are the best way for users to:
- ✅ Learn how to integrate Grizzly
- ✅ See guardrails in action
- ✅ Copy-paste working code
- ✅ Understand safety patterns

### Example Structure

Each example follows this structure:

```
examples/
├── README.md                          # Index of all examples
│
└── YOUR-SAFETY-SYSTEM/
    ├── README.md                      # Setup, API reference, troubleshooting
    ├── app.py                         # Full LLM app with guardrails (production-ready)
    ├── requirements.txt               # Dependencies
    ├── Dockerfile                     # Production image
    └── tests/
        └── test_app.py                # 10+ integration tests
```

### Adding a New Example

**Step 1: Create directory structure**

```bash
mkdir -p examples/YOUR-SAFETY-SYSTEM/tests
```

**Step 2: Implement LLM app with Grizzly guardrails (`app.py`)**

Requirements:
- ✅ Use FastAPI or another HTTP framework
- ✅ Integrate Grizzly guardrails (ingress, egress, or both)
- ✅ Include LLM integration (Claude, GPT-4, Llama, etc.)
- ✅ Use Pydantic for request/response validation
- ✅ Include comprehensive docstrings
- ✅ Handle errors gracefully
- ✅ Log guardrail decisions (pass/fail + reason)
- ✅ Runnable with `python app.py` (no CLI args)
- ✅ ~250-350 lines including comments

Example template:

```python
"""LLM Chat Service with Grizzly Guardrails."""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from grizzly import guard_ingress, guard_egress

app = FastAPI(title="LLM Chat with Guardrails")
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str

class ChatResponse(BaseModel):
    """Chat response model."""
    reply: str
    guardrails_passed: bool

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process chat with guardrails."""
    # Ingress guardrails (check prompt before sending to LLM)
    ingress_result = guard_ingress(request.message)
    if not ingress_result.passed:
        logger.warning(f"Prompt blocked: {ingress_result.reason}")
        raise HTTPException(status_code=400, detail=ingress_result.reason)
    
    # Call LLM
    response = call_llm(request.message)
    
    # Egress guardrails (validate output before returning)
    egress_result = guard_egress(response, config={"check_pii": True})
    if not egress_result.passed:
        logger.warning(f"Output failed guardrails: {egress_result.reason}")
        response = egress_result.repaired_output or "[Output failed safety checks]"
    
    return ChatResponse(
        reply=response,
        guardrails_passed=egress_result.passed
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 3: Create test suite (`tests/test_app.py`)**

Requirements:
- ✅ 10+ test cases
- ✅ Happy path (safe prompts)
- ✅ Guardrail blocks (injection attacks, jailbreaks)
- ✅ PII masking (outputs with sensitive data)
- ✅ JSON repair (malformed responses)
- ✅ Error handling (guardrail failures, LLM errors)
- ✅ Performance (latency benchmarks)

**Step 4: Create `requirements.txt`**

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
grizzly-guard==0.1.0
anthropic==0.7.1
requests==2.31.0
```

**Step 5: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["python", "app.py"]
```

**Step 6: Create detailed `README.md`**

Must include:

- 📝 **What It Does** — 1-2 paragraphs explaining the system
- 🏗️ **Architecture** — Diagram or text description
- 🚀 **Quick Start** — Install, run, test (5 steps max)
- 📡 **API Reference** — Request/response models with examples
- 🧪 **Test Suite Overview** — What each test case covers
- 🔧 **Troubleshooting** — Common errors and solutions
- ➡️ **Next Steps** — How to extend or modify the example

**Step 7: Test locally**

```bash
cd examples/YOUR-SAFETY-SYSTEM

# Install deps
pip install -r requirements.txt

# Run app
python app.py

# In another terminal, run tests
pytest tests/ -v

# All tests should pass ✅
```

**Step 8: Update examples index**

Edit [examples/README.md](examples/README.md) to add your example in the "Quick Links" section.

**Step 9: Submit PR**

```bash
git add examples/YOUR-SAFETY-SYSTEM/
git add examples/README.md
git commit -m "feat: Add YOUR-SAFETY-SYSTEM example"
gh pr create --title "feat: Add YOUR-SAFETY-SYSTEM example"
```

### Example Quality Checklist

Before submitting an example, verify:

- [ ] `app.py` is complete and production-ready (no TODOs)
- [ ] `app.py` uses LLM (Claude, GPT-4, Llama, etc.)
- [ ] `app.py` integrates Grizzly guardrails (ingress, egress, or both)
- [ ] `app.py` has comprehensive docstrings
- [ ] `app.py` handles errors and logs properly
- [ ] `app.py` logs guardrail decisions
- [ ] `requirements.txt` lists all dependencies with pinned versions
- [ ] `tests/test_app.py` has 10+ test cases
- [ ] Test cases cover safe prompts, attacks, PII, JSON repair, errors
- [ ] `Dockerfile` is production-ready
- [ ] `README.md` has all required sections
- [ ] `README.md` includes working Quick Start instructions
- [ ] All tests pass when running locally
- [ ] App runs with `python app.py` (no CLI args)
- [ ] Example is realistic and solves a real problem
- [ ] Code follows Ruff style guidelines (`ruff check --fix`)
- [ ] Example is added to [examples/README.md](examples/README.md)

### Example Ideas

Looking for example ideas? Consider:

- **Chat Safety** — FastAPI chat with ingress/egress guardrails
- **Content Moderation** — Check user-generated content for safety issues
- **Customer Support Bot** — Safe support agent with PII masking
- **Code Generation** — Generate code safely without injection vulnerabilities
- **Data Analysis Assistant** — Analyze data safely without leaking schema
- **Document Processing** — Extract info from documents without prompt injection
- **Multi-turn Workflows** — Complex agent workflows with guardrails at each step
- **Compliance Checker** — Ensure outputs meet regulatory requirements

## PR Workflow

### Before You Start

1. **Check for open PRs:** `gh pr list --state open`
2. **Verify main clean:** `git log main --oneline | head -1`
3. **Search codebase** for existing implementations (zero duplication policy):\
   ```bash
   rg "def check_" src/grizzly/core/
   find src/grizzly -name "*.py" -exec grep -l "def guard_" {} +
   ```
4. **Update issue label:** `status:backlog` → `status:in-progress` (if applicable)
5. **Create feature branch:** `git checkout -b feature/ISSUE-description`

### Commit Message Format

```
feat: Brief description (M1.X: Component if applicable)

Longer explanation of what changed and why.
Include test coverage summary.
Fixes #ISSUE_NUMBER.
```

### During Development

- Keep scope small: **Max 5 files per PR** (excludes lockfiles, generated files)
- Build frequently: `pytest tests/ --cov=src/grizzly`
- Run tests: `pytest tests/ -v`
- Update CHANGELOG.md with your changes

### Submitting PR

1. **Create PR via CLI:**
   ```bash
   git push origin feature/ISSUE-description
   gh pr create --title "feat: M1.X: Brief description" \
     --body "Detailed description, testing notes, architecture decisions"
   ```

2. **Wait for CI:** All checks must pass (ruff, pytest, type checking)

3. **Address feedback:** Push fixes to same branch (auto-updates PR)

4. **Merge:** Author squashes + merges (never fast-forward)
   ```bash
   gh pr merge <PR_NUMBER> --squash
   ```

5. **Delete branch** after merge:
   ```bash
   git branch -d feature/ISSUE-description
   git push origin --delete feature/ISSUE-description
   ```

## Release Process

### Version Bumping

Grizzly uses semantic versioning: **MAJOR.MINOR.PATCH**

- **MAJOR:** Breaking API changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Release Checklist

1. **Update version** in `pyproject.toml`:\
   ```toml
   [project]
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md** with release notes

3. **Tag commit:**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **Build and publish to PyPI:**
   ```bash
   pip install build twine
   python -m build
   twine upload dist/grizzly-guard-0.2.0-py3-none-any.whl
   ```

## Troubleshooting

### "ImportError: No module named 'grizz