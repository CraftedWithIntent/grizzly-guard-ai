"""LLM Proxy with Guardrails — Production-ready example.

Demonstrates Grizzly guardrails in a real FastAPI service that intercepts
LLM requests, detects prompt injections, masks PII, and validates JSON responses.
"""

import json
import logging
import os
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from grizzly_guard_ai.core import guard_egress, guard_ingress

logging.basicConfig(level=os.getenv("LOG_LEVEL", "info").upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Proxy with Guardrails",
    description="Production-ready proxy demonstrating Grizzly guardrails",
    version="1.0.0",
)

# Metrics for demonstration
metrics = {
    "total_requests": 0,
    "blocked_by_ingress": 0,
    "failed_egress": 0,
    "successful_completions": 0,
    "total_latency_ms": 0.0,
}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    """Guarded LLM endpoint.

    Intercepts /v1/chat/completions, applies Grizzly guards, forwards to
    upstream LLM, validates response with egress guards.

    Request Format (OpenAI-compatible):
    {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Your prompt here"}
        ]
    }

    Response Format:
    {
        "id": "chatcmpl-xxx",
        "choices": [{
            "message": {"role": "assistant", "content": "..."}
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        "guarded": true,
        "guard_result": {
            "injection_detected": false,
            "pii_masked": false,
            "latency_ms": 1.23
        }
    }
    """
    import time

    start_time = time.time()
    metrics["total_requests"] += 1

    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError as err:
        logger.error(f"Invalid JSON: {err}")
        return JSONResponse(
            {"error": "Invalid JSON"}, status_code=400
        )

    # Extract prompt from OpenAI format
    messages = body.get("messages", [])
    if not messages:
        return JSONResponse(
            {"error": "No messages"}, status_code=400
        )

    prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            prompt = msg.get("content", "")
            break

    if not prompt:
        return JSONResponse(
            {"error": "No user prompt"}, status_code=400
        )

    # === INGRESS GUARD: Check for injection ===
    logger.info(f"Scanning prompt: {prompt[:50]}...")
    ingress_result = guard_ingress(prompt)

    if not ingress_result.passed:
        metrics["blocked_by_ingress"] += 1
        logger.warning(
            f"BLOCKED: Injection detected. "
            f"Violations: {ingress_result.violations}, "
            f"Confidence: {ingress_result.confidence:.2f}"
        )
        return JSONResponse(
            {
                "error": "Request blocked by guardrails",
                "reason": "Prompt injection detected",
                "violations": ingress_result.violations,
                "confidence": ingress_result.confidence,
            },
            status_code=403,
        )

    # Update prompt with masked version (PII masked)
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content") == prompt:
            msg["content"] = ingress_result.masked_payload
            break

    logger.info(f"✓ Ingress guard passed ({ingress_result.latency_ms:.2f}ms)")

    # === MOCK LLM RESPONSE ===
    # In production, forward to real LLM (OpenAI, Anthropic, etc.)
    # For this example, we return a mock response
    mock_content = json.dumps({
        "response": "This is a demonstration response from Grizzly guardrails."
    })
    llm_response = {
        "id": "chatcmpl-example-001",
        "object": "chat.completion",
        "created": 1234567890,
        "model": body.get("model", "gpt-4"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 20,
            "total_tokens": len(prompt.split()) + 20,
        },
    }

    # === EGRESS GUARD: Validate LLM response ===
    response_text = llm_response["choices"][0]["message"]["content"]
    logger.info(f"Validating response: {response_text[:50]}...")

    egress_result = guard_egress(response_text)

    if not egress_result.passed:
        metrics["failed_egress"] += 1
        logger.error(
            f"Response validation failed: {egress_result.violations}"
        )
        return JSONResponse(
            {
                "error": "Response validation failed",
                "reason": str(egress_result.violations),
            },
            status_code=502,
        )

    # Use masked response (PII masked)
    llm_response["choices"][0]["message"]["content"] = (
        egress_result.masked_payload
    )
    logger.info(f"✓ Egress guard passed ({egress_result.latency_ms:.2f}ms)")

    # === RESPONSE ===
    metrics["successful_completions"] += 1
    elapsed_ms = (time.time() - start_time) * 1000
    metrics["total_latency_ms"] += elapsed_ms

    # Add guard metadata to response
    llm_response["guarded"] = True
    llm_response["guard_result"] = {
        "ingress_checked": True,
        "injection_confidence": ingress_result.confidence,
        "injection_detected": not ingress_result.passed,
        "pii_masked": ingress_result.masked_payload != prompt,
        "egress_validated": True,
        "total_latency_ms": elapsed_ms,
    }

    return JSONResponse(llm_response)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "guardrails": "active",
    }


@app.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """Return guardrail metrics."""
    avg_latency = (
        metrics["total_latency_ms"] / metrics["successful_completions"]
        if metrics["successful_completions"] > 0
        else 0
    )

    return {
        "total_requests": metrics["total_requests"],
        "successful_completions": metrics["successful_completions"],
        "blocked_by_ingress": metrics["blocked_by_ingress"],
        "failed_egress": metrics["failed_egress"],
        "avg_latency_ms": round(avg_latency, 2),
        "block_rate_percent": round(
            (
                (metrics["blocked_by_ingress"] + metrics["failed_egress"])
                / max(metrics["total_requests"], 1)
            )
            * 100,
            2,
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "9000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
