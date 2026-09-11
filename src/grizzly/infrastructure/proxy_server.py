"""Grizzly proxy server (FastAPI reverse proxy with guardrails).

Transparent HTTP proxy that intercepts LLM requests, applies ingress/egress
guards, and forwards to upstream providers (OpenAI, Anthropic, etc.).
"""

import logging

logger = logging.getLogger(__name__)


def run_proxy(port: int = 8081, host: str = "localhost", upstream_url: str = "") -> None:
    """Start Grizzly proxy server.

    Args:
        port: Server port (default: 8081)
        host: Server host/bind address (default: localhost)
        upstream_url: Upstream LLM API endpoint to proxy to

    Note:
        Phase 1: Stub implementation. Full proxy with guard composition
        in Phase 2 (M1.6.2).

    """
    raise NotImplementedError(
        "Proxy server implementation in M1.6.2. "
        "Currently validating architecture with core guards only."
    )
