# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in Grizzly Guard AI, please report it responsibly to:

📧 **Email:** hello@craftedwithintent.ai

**Please include:**
- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if you have one)

We will acknowledge receipt within 48 hours and provide updates on our progress toward a fix.

## Security Considerations

### What Grizzly Guard AI Protects Against

Grizzly Guard AI is designed as a **deterministic firewall layer** for LLM safety. It protects against:

- **Prompt Injection Attacks** — Detects and blocks common injection patterns
- **PII Leakage** — Redacts sensitive data (emails, phone numbers, SSNs, API keys)
- **Schema Violations** — Repairs and validates JSON output conformity
- **Jailbreak Patterns** — Identifies known jailbreak attempts

### What Grizzly Guard AI Does NOT Protect Against

Grizzly Guard AI is **NOT** a replacement for:

- **Model-level safety training** — Use model fine-tuning and RLHF for deeper safety
- **Application-level access controls** — Implement proper authentication and authorization
- **Data privacy compliance** — Grizzly Guard AI can help with PII masking, but doesn't replace encryption or compliance frameworks
- **Complete prompt injection defense** — Use Grizzly Guard AI + application-level validation together

### Best Practices

When using Grizzly Guard AI in production:

1. **Combine with application-level validation** — Don't rely solely on Grizzly Guard AI
2. **Keep guardrail rules updated** — Regularly review and update detection patterns
3. **Monitor false positives/negatives** — Log and analyze edge cases
4. **Use HTTPS/TLS** — Encrypt data in transit
5. **Run locally when possible** — Minimize external API dependencies
6. **Test edge cases** — Include security tests in your CI/CD pipeline
7. **Review Grizzly Guard AI updates** — Subscribe to security advisories

## Known Limitations

### Deterministic vs. Adaptive Defense

Grizzly Guard AI uses **deterministic rules** (regex, semantic checks, schema validation) for speed (<5ms latency). This means:

- ✅ **Fast:** Runs locally without cloud calls
- ✅ **Predictable:** Same input → same output
- ⚠️ **Limited:** Can't adapt to novel attack patterns like an LLM-based guardrail

For cutting-edge threat detection, combine Grizzly Guard AI with periodic LLM-based reviews.

### Regex-Based Detection

Grizzly Guard AI includes regex patterns for common prompt injection attacks. Attackers may:
- Use encoding (base64, HTML entities)
- Obfuscate payloads
- Use natural language variations

Mitigation: Combine Grizzly Guard AI's regex patterns with semantic similarity checks and periodic security audits.

## Security Updates

We follow [semantic versioning](https://semver.org/) for releases:

- **MAJOR:** Breaking changes or critical security fixes
- **MINOR:** New features or security improvements
- **PATCH:** Bug fixes and security patches

Subscribe to GitHub releases to stay informed of security updates:
https://github.com/CraftedWithIntent/grizzly/releases

## Dependencies

Grizzly Guard AI depends on well-maintained libraries:
- **FastAPI** — Industry-standard async web framework
- **Pydantic** — Validated data models
- **ONNX Runtime** — Local ML inference (no cloud calls)
- **httpx** — Secure HTTP client

We regularly audit and update dependencies. Report dependency vulnerabilities via security@craftedwithintent.ai.

## Testing & Validation

Grizzly Guard AI includes comprehensive security tests:

```bash
pytest tests/ -v --cov=src/grizzly
```

All PR reviews include:
- Code review for security issues
- Type checking (strict pyright mode)
- Linting (Ruff)
- Coverage validation (80%+ required)

## Compliance Notes

### Data Retention

Grizzly Guard AI **does not store or transmit data** by default. All processing happens in-process or in-memory. If you use the proxy server, review your deployment configuration for data retention policies.

### PII Handling

Grizzly Guard AI can redact PII before it's logged or transmitted downstream. However:
- Always review masked output for accuracy
- Test with your specific PII patterns
- Combine with other privacy measures (encryption, access controls, etc.)

### Third-Party Integrations

If you deploy Grizzly Guard AI in front of a cloud LLM API (OpenAI, Anthropic, etc.):
- Data flows: Your app → Grizzly Guard AI → Cloud API
- Grizzly Guard AI **does not log** requests to cloud APIs (configurable)
- Review the cloud provider's data retention policies

---

**Questions?** Open a GitHub Discussion or email hello@craftedwithintent.ai
