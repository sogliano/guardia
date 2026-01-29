# ---------- builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

COPY . .

# ---------- runtime ----------
FROM python:3.11-slim

RUN groupadd -r guardia && useradd -r -g guardia -s /sbin/nologin guardia

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build /app

RUN mkdir -p /app/quarantine_store /app/ml_models && \
    chown -R guardia:guardia /app

USER guardia

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
