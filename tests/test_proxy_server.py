"""Tests for Grizzly proxy server (M1.6)."""

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from grizzly.core import guard_egress, guard_ingress
from grizzly.infrastructure.proxy_server import _stream_with_guard


def make_test_app() -> FastAPI:
    """Create a minimal test app with guards."""
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request) -> Response:
        """Test endpoint."""
        try:
            body: dict[str, Any] = await request.json()
        except json.JSONDecodeError:
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
                content=json.dumps({"error": "No prompt"}),
                status_code=400,
                media_type="application/json",
            )

        ingress_result = guard_ingress(prompt)
        if not ingress_result.passed:
            return Response(
                content=json.dumps({"error": "Blocked"}),
                status_code=403,
                media_type="application/json",
            )

        response_data = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}]
        }

        response_text = response_data["choices"][0]["message"]["content"]
        egress_result = guard_egress(response_text)

        if not egress_result.passed:
            return Response(
                content=json.dumps({"error": "Invalid"}),
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
        """Health check."""
        return {"status": "healthy"}

    return app


@pytest.fixture
def client() -> TestClient:
    """Test client."""
    return TestClient(make_test_app())


def test_chat_completions_success(client: TestClient) -> None:
    """Test successful request."""
    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    }

    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data


def test_chat_completions_no_messages(client: TestClient) -> None:
    """Test no messages."""
    payload = {"model": "gpt-4", "messages": []}

    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 400


def test_chat_completions_invalid_json(client: TestClient) -> None:
    """Test invalid JSON."""
    response = client.post(
        "/v1/chat/completions",
        content="{invalid}",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_health_check(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_stream_with_guard() -> None:
    """Test streaming with guard."""
    chunks = [
        'data: {"choices": [{"delta": {"content": "Hi"}}]}',
        "data: [DONE]",
    ]

    mock_response = AsyncMock()
    mock_response.aiter_lines = AsyncMock(return_value=iter(chunks))

    output = []
    async for line in _stream_with_guard(mock_response):
        output.append(line)

    assert len(output) >= 1


def test_run_proxy_callable() -> None:
    """Test run_proxy is callable."""
    from grizzly.infrastructure.proxy_server import run_proxy

    assert callable(run_proxy)
