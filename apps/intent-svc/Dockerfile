# Multi-stage production container for Intent Classifier Microservice (Spec §3.2.5)
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:0.5.15 /uv /bin/uv

COPY apps/intent-svc/requirements.txt requirements.txt
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -r requirements.txt

FROM python:3.14-slim AS runner

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    AIP_HTTP_PORT=8000 \
    AIP_HEALTH_ROUTE=/v1/health \
    AIP_PREDICT_ROUTE=/v1/classify

# Copy model artifacts and code
COPY ml/intent ml/intent
COPY apps/intent-svc/main.py main.py

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')" || exit 1

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
