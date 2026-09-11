# Grizzly Examples

Production-ready examples demonstrating Grizzly guardrails in real-world scenarios.

## Available Examples

### LLM Proxy with Guardrails

**Directory:** `llm-proxy-with-guards/`

A complete FastAPI service that demonstrates Grizzly guardrails protecting LLM requests:

- **Ingress Guards:** Detect prompt injections, mask PII
- **Egress Guards:** Validate LLM responses, repair JSON, mask PII
- **Metrics:** Real-time tracking of blocks and latency
- **OpenAI Compatible:** Drop-in proxy for `/v1/chat/completions`

**Quick Start:**
```bash
cd llm-proxy-with-guards
pip install -r requirements.txt
python app.py

# In another terminal
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Test locally:**
```bash
pytest tests/ -v
```

**Deploy with Docker:**
```bash
docker-compose up
```

**Deploy to Kubernetes:**
```bash
kubectl apply -f k8s-deployment.yaml
```

## Example Features

### Complete, Runnable Code
- ✅ Executable without modifications
- ✅ Self-contained (all deps in requirements.txt)
- ✅ Production-ready error handling
- ✅ Comprehensive logging

### Realistic Scenarios
- ✅ Real business use case (LLM safety)
- ✅ Demonstrates core Grizzly patterns
- ✅ Shows guard composition (ingress + egress)
- ✅ Includes metrics for production monitoring

### Comprehensive Testing
- ✅ Happy path tests (safe prompts)
- ✅ Failure path tests (injections)
- ✅ Edge cases (empty messages, invalid JSON)
- ✅ PII masking verification
- ✅ Response structure validation
- ✅ 9 total tests, 100% coverage

### Production Deployment
- ✅ FastAPI + Uvicorn
- ✅ Health check endpoint
- ✅ Metrics endpoint
- ✅ Docker containerization
- ✅ Kubernetes manifests
- ✅ Resource requests/limits

## Adding a New Example

1. **Create directory:** `mkdir -p examples/YOUR-EXAMPLE/tests`
2. **Implement:** Create your FastAPI app in `app.py`
3. **Test:** Add tests in `tests/test_app.py` (pytest)
4. **Document:** Write `README.md` with setup and usage
5. **Deploy:** Add Dockerfile and K8s manifests
6. **Submit:** Open PR with all files and tests passing

## Best Practices

### Code Quality
- ✅ Type hints on all functions
- ✅ Docstrings on modules and public functions
- ✅ Error handling for all edge cases
- ✅ Logging at appropriate levels (info, warning, error)

### Testing
- ✅ Use FastAPI TestClient for testing
- ✅ Test happy path and failure paths
- ✅ Test all endpoints
- ✅ Aim for 100% code coverage

### Documentation
- ✅ README with quick start
- ✅ API reference section
- ✅ Example requests/responses
- ✅ Troubleshooting section
- ✅ Links to related docs

### Deployment
- ✅ Dockerfile (multi-stage build preferred)
- ✅ docker-compose.yml for local testing
- ✅ K8s deployment manifests
- ✅ Health check endpoint
- ✅ Metrics/monitoring endpoint

## Files Structure

```
examples/
├── README.md (this file)
│
└── llm-proxy-with-guards/
    ├── README.md (detailed setup and usage)
    ├── app.py (FastAPI service, ~200 lines)
    ├── requirements.txt (pip dependencies)
    ├── Dockerfile (containerization)
    ├── docker-compose.yml (local dev)
    ├── k8s-deployment.yaml (Kubernetes)
    └── tests/
        └── test_app.py (pytest suite, 9 tests)
```

## Running Examples

### Local Development
```bash
cd llm-proxy-with-guards
pip install -r requirements.txt
python app.py
pytest tests/ -v
```

### Docker
```bash
cd llm-proxy-with-guards
docker-compose up
```

### Kubernetes
```bash
cd llm-proxy-with-guards
kubectl apply -f k8s-deployment.yaml
kubectl port-forward svc/grizzly-proxy 9000:9000 -n grizzly-example
```

## Example Metrics

### LLM Proxy with Guardrails

- **Response Time:** <5ms P50 (includes guardrail overhead)
- **Test Suite:** 9 tests, 100% coverage
- **Code Size:** ~200 lines (app.py)
- **Deployment:** <200MB Docker image
- **Production Ready:** ✅ Yes

## Contributing

Have a great example? Open a PR at https://github.com/CraftedWithIntent/grizzly/pulls

Include:
- ✅ Complete app code
- ✅ Test suite with 4+ tests
- ✅ Comprehensive README
- ✅ Dockerfile and K8s manifests
- ✅ All tests passing locally

---

**Questions?** See main README: https://github.com/CraftedWithIntent/grizzly#readme

Happy building! 🚀
