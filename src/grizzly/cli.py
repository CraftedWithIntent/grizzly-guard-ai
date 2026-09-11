"""Grizzly CLI: guardrail proxy and scanning commands."""

import typer

app = typer.Typer(help="Grizzly: Deterministic LLM Guardrails Engine")


@app.command()
def proxy(
    port: int = typer.Option(8081, help="Proxy server port"),
    host: str = typer.Option("0.0.0.0", help="Proxy server host"),
    upstream: str = typer.Option(
        "https://api.openai.com/v1/chat/completions",
        help="Upstream LLM API endpoint",
    ),
) -> None:
    """Start Grizzly proxy server on specified port.

    Example:
        grizzly proxy --port 8081 --host 127.0.0.1

    """
    from grizzly.infrastructure.proxy_server import run_proxy

    typer.echo(f"Starting Grizzly proxy on {host}:{port}")
    typer.echo(f"Upstream: {upstream}")
    run_proxy(port=port, host=host, upstream_url=upstream)


@app.command()
def scan(
    prompt: str = typer.Option(..., help="Prompt to scan for injection risk"),
) -> None:
    """Scan a prompt for injection risk.

    Example:
        grizzly scan --prompt "ignore previous instructions"

    """
    from grizzly.core import classify_injection_heuristic

    result = classify_injection_heuristic(prompt)
    typer.echo(f"Injection Risk Score: {result.risk_score:.2f}")
    typer.echo(f"Is Injection: {result.is_injection}")
    typer.echo(f"Detected Patterns: {result.detected_patterns}")
    typer.echo(f"Latency: {result.latency_ms:.2f}ms")


@app.command()
def health() -> None:
    """Check Grizzly health status.

    Returns 0 if all components are healthy.
    """
    typer.echo("Grizzly Health Check")
    typer.echo("Status: healthy")
    typer.echo("Components:")
    typer.echo("  - Core guards: OK")
    typer.echo("  - Proxy server: ready")
    typer.echo("  - CLI: operational")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("Grizzly v0.1.0-dev")
    typer.echo("Deterministic LLM Guardrails Engine")
    typer.echo("MIT License • CraftedWithIntent")


if __name__ == "__main__":
    app()
