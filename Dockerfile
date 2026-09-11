# Multi-stage build for Grizzly guardrails proxy
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source and build wheel
COPY . .
RUN pip install --upgrade pip uv && \
    uv build --wheel && \
    mv dist/*.whl /tmp/grizzly.whl

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 grizzly

# Install runtime dependencies only
RUN pip install --upgrade pip && \
    pip install --no-cache-dir /tmp/grizzly.whl

# Copy wheel from builder
COPY --from=builder /tmp/grizzly.whl .

# Set ownership
RUN chown -R grizzly:grizzly /app

# Switch to non-root user
USER grizzly

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -m grizzly.cli health || exit 1

# Default command: start proxy on :8081
ENTRYPOINT ["python", "-m", "grizzly.cli"]
CMD ["proxy", "--host", "0.0.0.0", "--port", "8081"]

# Expose proxy port
EXPOSE 8081
