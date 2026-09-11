FROM python:3.11-slim

WORKDIR /app

# Install grizzly-guard from PyPI
RUN pip install --upgrade pip && \
    pip install grizzly-guard fastapi uvicorn

# Copy example app
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9000/health')" || exit 1

# Run app
EXPOSE 9000
CMD ["python", "app.py"]
