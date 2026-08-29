# Multi-stage Dockerfile for Grizzly guardrails engine

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV and build Grizzly
COPY . .
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.cargo/bin/uv pip install --system -e . && \
    python -m pip install build && \
    python -m build

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files from builder
COPY --from=builder /build/dist /tmp/dist

# Install Grizzly from built wheel
RUN pip install --no-cache-dir /tmp/dist/grizzly_guard*.whl && \
    rm -rf /tmp/dist

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run Grizzly proxy
EXPOSE 8081
CMD ["grizzly", "proxy", "--host", "0.0.0.0", "--port", "8081"]
