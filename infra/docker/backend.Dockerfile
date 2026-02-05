# ── Stage 1: Install dependencies ──
FROM python:3.11-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (saves ~1.5GB vs full torch)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy only dependency spec — this layer is cached until pyproject.toml changes
COPY backend/pyproject.toml .

# Install dependencies only (not the package itself, since app/ doesn't exist yet)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    "asyncpg>=0.30.0" \
    "alembic>=1.14.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.0.0" \
    "PyJWT[crypto]>=2.8.0" \
    "clerk-backend-api>=1.0.0" \
    "httpx>=0.27.0" \
    "transformers>=4.46.0" \
    "openai>=1.55.0" \
    "python-multipart>=0.0.12" \
    "structlog>=24.4.0" \
    "aiosmtpd>=1.4.6" \
    "aiosmtplib>=3.0.0" \
    "slowapi>=0.1.9"

# ── Stage 2: Final slim image with security improvements ──
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r guardia && useradd -r -g guardia -s /sbin/nologin guardia

WORKDIR /app

# Copy installed packages from deps stage (no build-essential in final image)
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ .

# Create directories and set permissions
RUN mkdir -p /app/quarantine_store /app/ml_models && \
    chown -R guardia:guardia /app

# Pre-download ML model to avoid cold starts
# Uses the python environment with transformers installed
ARG ML_MODEL_REPO="guardia-project/distilbert-guardia-v2"
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    model_name = '${ML_MODEL_REPO}'; \
    print(f'Downloading {model_name}...'); \
    AutoTokenizer.from_pretrained(model_name).save_pretrained('/app/ml_models/distilbert-guardia'); \
    AutoModelForSequenceClassification.from_pretrained(model_name).save_pretrained('/app/ml_models/distilbert-guardia'); \
    print('Model downloaded successfully.')" && \
    chown -R guardia:guardia /app/ml_models

# Switch to non-root user
USER guardia

EXPOSE 8000

# Add healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Use multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
