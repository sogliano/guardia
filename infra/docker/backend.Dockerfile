# ── Stage 1: Install dependencies ──
FROM python:3.11-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (saves ~1.5GB vs full torch)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy dependency spec and minimal package structure for pip install
COPY backend/pyproject.toml .
RUN mkdir -p app && touch app/__init__.py

# Install all dependencies including ML extras
RUN pip install --no-cache-dir ".[ml]"

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

# Switch to non-root user
USER guardia

EXPOSE 8000

# Add healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Use multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
