"""Grizzly proxy server (FastAPI reverse proxy with guardrails).

Transparent HTTP proxy that intercepts LLM requests, applies ingress/egress
guards, and forwards to upstream providers (OpenAI, Anthropic, etc.).
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

from grizzly.core import guard_egress, guard_ingress

logger = logging.getLogger(__name__)


def run_proxy(  # noqa: C901
    port: int = 8081, host: str = "localhost", upstream_url: str = ""
) -> None:
    """Start Grizzly proxy server.

    Args:
        port: Server port (default: 8081)
        host: Server host/bind address (default: localhost)
        upstream_url: Upstream LLM API endpoint to proxy to

    """
    import uvicorn

    app = FastAPI(title="Grizzly Proxy", description="LLM guardrails proxy")

    @app.post("/v1/chat/completions")  # noqa: C901
    async def chat_completions(request: Request) -> Response:  # noqa: C901
        """OpenAI-compatible chat completions endpoint.

        Applies ingress/egress guards to LLM requests.
        """
        try:
            body: dict[str, Any] = await request.json()
        except json.JSONDecodeError as err:
            logger.error(f"Invalid JSON: {err}")
            return Response(
                content=json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                media_type="application/json",
            )

        messages = body.get("messages", [])
        if not messages:
            return Response(
                content=json.dumps({"error": "No messages"}),
                status_code=400,
                media_type="application/json",
            )

        prompt = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break

        if not prompt:
            return Response(
                content=json.dumps({"error": "No user prompt"}),
                status_code=400,
                media_type="application/json",
            )

        # Apply ingress guard
        ingress_result = guard_ingress(prompt)
        if not ingress_result.passed:
            logger.warning(f"Ingress blocked: {ingress_result.violations}")
            return Response(
                content=json.dumps(
                    {
                        "error": "Request blocked",
                        "reason": str(ingress_result.violations),
                    }
                ),
                status_code=403,
                media_type="application/json",
            )

        # Update prompt with masked version
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content") == prompt:
                msg["content"] = ingress_result.masked_payload
                break

        # Forward to upstream
        stream = body.get("stream", False)
        async with httpx.AsyncClient() as client:
            try:
                resp: httpx.Response = await client.post(
                    upstream_url, json=body, stream=stream  # type: ignore[call-arg]
                )
            except httpx.RequestError as err:
                logger.error(f"Upstream failed: {err}")
                return Response(
                    content=json.dumps({"error": "Upstream unavailable"}),
                    status_code=502,
                    media_type="application/json",
                )

        if stream:
            return StreamingResponse(
                _stream_with_guard(resp),  # type: ignore[arg-type]
                media_type="text/event-stream",
            )

        try:
            response_data: dict[str, Any] = resp.json()  # type: ignore[union-attr]
        except json.JSONDecodeError:
            logger.error("Invalid upstream JSON")
            return Response(
                content=json.dumps({"error": "Invalid response"}),
                status_code=502,
                media_type="application/json",
            )

        # Apply egress guard
        response_text: str = ""
        if "choices" in response_data and response_data["choices"]:
            response_text = response_data["choices"][0].get(
                "message", {}
            ).get("content", "")

        if response_text:
            egress_result = guard_egress(response_text)
            if not egress_result.passed:
                logger.warning(f"Egress failed: {egress_result.violations}")
                return Response(
                    content=json.dumps(
                        {
                            "error": "Validation failed",
                            "reason": str(egress_result.violations),
                        }
                    ),
                    status_code=502,
                    media_type="application/json",
                )
            response_data["choices"][0]["message"]["content"] = (
                egress_result.masked_payload
            )

        return Response(
            content=json.dumps(response_data),
            status_code=200,
            media_type="application/json",
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    uvicorn.run(app, host=host, port=port, log_level="info")


async def _stream_with_guard(response: httpx.Response) -> AsyncIterator[str]:
    """Stream with egress guard on each chunk.

    Args:
        response: Upstream response

    Yields:
        Guarded chunks

    """
    async for line in response.aiter_lines():
        if not line or line.startswith(":"):
            yield line + "\n"
            continue

        if line.startswith("data: "):
            try:
                data_str = line[6:]
                if data_str == "[DONE]":
                    yield line + "\n"
                    continue

                chunk = json.loads(data_str)
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        guard_result = guard_egress(token)
                        if guard_result.passed:
                            delta["content"] = guard_result.masked_payload
                            chunk["choices"][0]["delta"] = delta

                yield "data: " + json.dumps(chunk) + "\n"
            except json.JSONDecodeError:
                logger.error(f"Parse failed: {line}")
                yield line + "\n"
        else:
            yield line + "\n"
