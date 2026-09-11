"""Tests for Grizzly proxy server (M1.6)."""

from grizzly.infrastructure.proxy_server import run_proxy


def test_run_proxy_callable() -> None:
    """Test run_proxy is callable."""
    assert callable(run_proxy)


def test_run_proxy_signature() -> None:
    """Test run_proxy has correct signature."""
    import inspect

    sig = inspect.signature(run_proxy)
    assert "port" in sig.parameters
    assert "host" in sig.parameters
    assert "upstream_url" in sig.parameters

    # Check defaults
    assert sig.parameters["port"].default == 8081
    assert sig.parameters["host"].default == "localhost"
    assert sig.parameters["upstream_url"].default == ""


def test_run_proxy_not_implemented() -> None:
    """Test run_proxy raises NotImplementedError in Phase 1."""
    import pytest

    with pytest.raises(NotImplementedError, match="M1.6.2"):
        run_proxy(upstream_url="http://localhost:8000")
