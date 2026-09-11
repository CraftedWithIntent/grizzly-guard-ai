"""Infrastructure layer: proxy server, ONNX runtime, SIEM exporter.

Phase 1: Stub implementations. Phase 1+ fills in FastAPI proxy, ONNX model
loader, and OpenTelemetry/Splunk security event emission.
"""

from grizzly.infrastructure import proxy_server

__all__ = ["proxy_server"]
