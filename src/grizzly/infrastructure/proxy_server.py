"""Grizzly proxy server (Phase 1 stub).

FastAPI reverse proxy for LLM guardrails. Intercepts requests, applies
ingress/egress rules, forwards to upstream LLM API.
"""


def run_proxy(port: int, host: str, upstream_url: str) -> None:
    """Start Grizzly proxy server.

    Args:
        port: Server port
        host: Server host/bind address
        upstream_url: Upstream LLM API endpoint to proxy to

    """
    raise NotImplementedError("Phase 1 stub: Proxy server implementation pending")
