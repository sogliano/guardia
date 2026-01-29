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
RUN pip install --no-cache-dir .

# ── Stage 2: Final slim image ──
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from deps stage (no build-essential in final image)
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
