<p align="center">
  <img src="docs/assets/logo.png" alt="Guard-IA" width="120" />
</p>

<h1 align="center">Guard-IA</h1>

<p align="center">
  <strong>AI-powered pre-delivery email fraud detection middleware</strong><br/>
  Phishing, BEC & impersonation detection for Google Workspace
</p>

<p align="center">
  <a href="README.es.md">Español</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#architecture">Architecture</a> &middot;
  <a href="#development">Development</a> &middot;
  <a href="#deployment">Deployment</a>
</p>

---

## Overview

Guard-IA is a **pre-delivery email security system** that intercepts inbound emails before they reach Google Workspace inboxes. Every email is analyzed through a **3-layer AI pipeline** (heuristics + ML + LLM) producing a unified threat score and actionable verdict in under 5 seconds.

**Built as a university thesis (ORT Uruguay) for [Strike Security](https://strike.sh).**

### Key Features

- ⚡ **Sub-5-second pipeline** -- real-time analysis without delivery delays
- 🛡️ **3-layer defense** -- heuristics (5ms) → ML (18ms) → LLM (2-3s)
- 🎯 **Pre-delivery interception** -- analyzes before inbox, not after
- 📊 **Analyst dashboard** -- case management, quarantine review, threat analytics
- 🔄 **Graceful degradation** -- auto-adjusts when layers unavailable
- 🚨 **Slack alerts** -- instant notifications for high-risk detections

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (local or [Neon](https://neon.tech))
- Docker & Docker Compose (optional)

### Local Development (5 minutes)

> **Windows users:** See the [Windows setup section](#windows) below for PowerShell-specific commands.

```bash
# 1. Clone repository
git clone https://github.com/your-org/guardia.git
cd guardia

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials (DB, Clerk, OpenAI, Slack)
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with VITE_API_BASE_URL and VITE_CLERK_PUBLISHABLE_KEY

# 3. Start all services (recommended — macOS/Linux only)
make dev

# OR manually:
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
alembic upgrade head
PYTHONPATH=$PWD uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Seed Test Data

```bash
cd backend
python -m scripts.seed_emails
```

---

## Architecture

```
┌─────────────┐
│ Inbound     │
│ Email       │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────┐
│ SMTP Gateway (aiosmtpd :2525)          │
└──────┬──────────────────────────────────┘
       │
       v
┌─────────────────────────────────────────┐
│ Detection Pipeline                       │
│ ┌─────────────────────────────────────┐ │
│ │ 1. Heuristics (~5ms)        [30%]  │ │
│ │    SPF/DKIM/DMARC, typosquat, URLs │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 2. ML Classifier (~18ms)    [50%]  │ │
│ │    DistilBERT fine-tuned (66M)     │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 3. LLM Analyst (~2-3s)      [20%]  │ │
│ │    OpenAI GPT risk assessment      │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ Final Score = Σ(layer_score × weight)   │
└──────┬───────────────────────────────────┘
       │
       v
┌──────────────────┬─────────────────────┐
│ Verdict Decision │ Threshold           │
├──────────────────┼─────────────────────┤
│ ALLOWED          │ < 0.3               │
│ WARNED           │ 0.3 - 0.6           │
│ QUARANTINED      │ 0.6 - 0.8           │
│ BLOCKED          │ ≥ 0.8               │
└──────────────────┴─────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL 16 |
| **Frontend** | Vue 3 (Composition API), TypeScript, Pinia, Vite |
| **ML** | DistilBERT (66M params), HuggingFace Hub, MLflow tracking |
| **Auth** | Clerk (RS256 JWT, invitation-only) |
| **SMTP Gateway** | GCE VM (aiosmtpd :25, detection pipeline, Gmail API delivery) |
| **Hosting** | Cloud Run (API), Vercel (SPA), Neon (DB), GCE VM (SMTP) |
| **Email Delivery** | Gmail API `users.messages.import` (primary), SMTP relay (fallback) |
| **LLM** | OpenAI GPT-4o-mini |

### Project Structure

```
guardia/
├── backend/              # Python 3.11 / FastAPI
│   ├── app/
│   │   ├── api/v1/       # REST endpoints (cases, emails, dashboard, etc.)
│   │   ├── services/     # Business logic + detection pipeline
│   │   ├── models/       # SQLAlchemy ORM (16 tables)
│   │   ├── gateway/      # SMTP server, Gmail API delivery, internal API
│   │   └── db/           # Alembic migrations
│   ├── tests/            # pytest + pytest-asyncio
│   └── pyproject.toml
├── frontend/             # Vue 3 / TypeScript / Vite
│   ├── src/
│   │   ├── views/        # Page components (7)
│   │   ├── components/   # Reusable UI
│   │   ├── stores/       # Pinia state (7 stores)
│   │   └── services/     # Axios API clients
│   ├── tests/            # Vitest + Playwright
│   └── package.json
├── ml/                   # DistilBERT fine-tuning
│   ├── src/              # Training pipeline
│   ├── data/             # Datasets (raw/processed/splits)
│   └── models/           # Saved model weights
├── infra/                # Docker, Nginx configs
├── docs/                 # Architecture, API, deployment, testing guides
├── docker-compose.yml
└── Makefile
```

---

## Development

### Local Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend (Vite) | 3000 | http://localhost:3000 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| SMTP Gateway | 2525 | localhost:2525 |
| PostgreSQL | 5432 | localhost:5432 |
| MLflow | 5000 | http://localhost:5000 |

### Make Commands

> `make` commands require GNU Make and are designed for **macOS/Linux**. On Windows, use the manual commands below.

```bash
make dev              # Start all services (db, mlflow, backend, frontend)
make test             # Run all tests (backend + frontend)
make lint             # ruff + mypy + eslint
make migrate          # Apply Alembic migrations
make migration msg="" # Create new migration
make clean            # Stop all services
```

### Manual Commands

**Backend (macOS/Linux):**
```bash
cd backend
source .venv/bin/activate

# Run server
PYTHONPATH=$PWD uvicorn app.main:app --reload --port 8000

# Run tests
pytest --cov=app --cov-report=term-missing

# Lint
ruff check app
mypy app

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**Backend (Windows PowerShell):**
```powershell
cd backend

# First time: create venv and install deps
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Run migrations
$env:PYTHONPATH = "."
.venv\Scripts\alembic.exe upgrade head

# Run server (foreground)
$env:PYTHONPATH = "."
.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
$env:PYTHONPATH = "."
.venv\Scripts\pytest.exe --cov=app --cov-report=term-missing

# Lint
.venv\Scripts\ruff.exe check app
.venv\Scripts\mypy.exe app
```

> **Note:** On Windows with `AllSigned` PowerShell execution policy, use the `.exe` binaries
> directly (e.g. `.venv\Scripts\python.exe`) instead of activating the venv via `Activate.ps1`.
> `npm` must be called as `npm.cmd` in PowerShell.

**Frontend (macOS/Linux):**
```bash
cd frontend

# Dev server
npm run dev

# Tests
npm run test          # Vitest unit tests
npm run test:e2e      # Playwright E2E tests

# Lint
npm run lint
npm run type-check

# Build
npm run build
npm run preview       # Preview production build
```

**Frontend (Windows PowerShell):**
```powershell
cd frontend

# Install deps
npm.cmd install

# Dev server
npm.cmd run dev

# Tests
npm.cmd run test
npm.cmd run test:e2e

# Build
npm.cmd run build
```

### Environment Variables

Create `.env.local` from `.env.example`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/guardia

# Clerk Auth (https://clerk.com)
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."

# OpenAI (https://platform.openai.com)
OPENAI_API_KEY=sk-proj-...

# Slack (optional, for alerts)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# App Config
APP_ENV=local
APP_DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
RATE_LIMIT_PER_MINUTE=1000
```

### Code Style

**Python (backend):**
- 4-space indent, 100 char line length
- Linters: `ruff check` (E, F, I, N, W), `mypy`
- All async (SQLAlchemy async, asyncpg, httpx)
- Tests: `pytest` + `pytest-asyncio` (asyncio_mode=auto)

**TypeScript/Vue (frontend):**
- 2-space indent
- `<script setup lang="ts">` composition API
- Path alias: `@/` → `src/`

**General:**
- LF line endings, UTF-8, trim trailing whitespace, final newline
- Imports always at top (never mid-code)
- Commits: brief, one line, Spanish or English

---

## Deployment

### Environments

| Environment | Backend | Frontend | Database | Branch |
|-------------|---------|----------|----------|--------|
| **Local** | localhost:8000 | localhost:3000 | Local/Neon | any |
| **Staging** | Cloud Run (us-east1) | Vercel (preview) | Neon (shared) | `staging` |
| **Production** | Cloud Run | Vercel (production) | Neon (dedicated) | `main` |

### Staging Deployment

**Automatic (via GitHub Actions):**
```bash
git checkout staging
git merge feat/your-branch
git push origin staging
# Triggers deploy-backend-staging.yml + deploy-frontend-staging.yml
```

**Backend:**
- Runs tests (`pytest --cov`)
- Builds Docker image
- Deploys to Cloud Run (us-east1)
- Uses `.env.staging` secrets from GCP Secret Manager

**Frontend:**
- Runs tests (`vitest` + `playwright`)
- Builds production bundle
- Deploys to Vercel preview

**URLs:**
- Backend: https://guardia-backend-staging-xxxxx.run.app
- Frontend: https://guardia-staging.vercel.app

### Production Deployment

**Automatic (via GitHub Actions):**
```bash
git checkout main
git merge staging
git push origin main
# Triggers deploy-backend-production.yml + deploy-frontend-production.yml
```

**Safety checks:**
- Only `main` branch can deploy to production
- All tests must pass (coverage ≥60% backend)
- Manual approval for production frontend deploy

**URLs:**
- Backend: https://guardia-backend-xxxxx.run.app
- Frontend: https://guardia.strike.sh

### Environment Files

**DO NOT commit `.env.*` files with real secrets!**

Configuration files are loaded based on `APP_ENV`:

```
.env.local       → development (local)
.env.staging     → staging (Cloud Run)
.env.production  → production (Cloud Run)
.env.example     → template (safe to commit)
```

**Use GCP Secret Manager for staging/production:**
```bash
# Set secret
gcloud secrets create CLERK_SECRET_KEY --data-file=-

# Access in Cloud Run
# Set environment variable: CLERK_SECRET_KEY=projects/PROJECT_ID/secrets/CLERK_SECRET_KEY/versions/latest
```

### Manual Deployment

**Backend (Cloud Run):**
```bash
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/guardia-backend
gcloud run deploy guardia-backend \
  --image gcr.io/PROJECT_ID/guardia-backend \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production
```

**Frontend (Vercel):**
```bash
cd frontend
vercel --prod
```

---

## API Reference

**Base URL:** `https://guardia-backend-xxxxx.run.app/api/v1` (production)
**Auth:** Bearer token (Clerk RS256 JWT)

### Core Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/health` | Health check | ❌ |
| `GET` | `/auth/me` | Current user profile | ✅ |
| `POST` | `/emails/ingest` | Ingest new email | ✅ |
| `GET` | `/emails` | List emails (paginated) | ✅ |
| `GET` | `/emails/:id` | Email detail | ✅ |
| `GET` | `/cases` | List cases (filtered) | ✅ |
| `GET` | `/cases/:id` | Case detail | ✅ |
| `POST` | `/cases/:id/resolve` | Resolve case (final verdict) | ✅ Analyst |
| `POST` | `/cases/:id/notes` | Add investigation note | ✅ |
| `GET` | `/dashboard` | Dashboard statistics | ✅ |
| `GET` | `/quarantine` | List quarantined emails | ✅ |
| `POST` | `/quarantine/:id/release` | Release from quarantine | ✅ Analyst |
| `POST` | `/quarantine/:id/delete` | Delete quarantined email | ✅ Analyst |
| `GET` | `/monitoring` | Pipeline monitoring (LLM/ML/Heuristics) | ✅ |

**Full API docs:** https://guardia-backend-xxxxx.run.app/docs (Swagger UI)

### Rate Limits

| Endpoint | Limit | Reason |
|----------|-------|--------|
| Critical actions (delete, release, fp-review) | 3-5/min | Irreversible operations |
| Modifications (resolve, notes) | 10-30/min | Important changes |
| Complex reads (dashboard, monitoring) | 30-60/min | Heavy SQL queries |
| Simple reads (get case, email) | 100/min | Lightweight |
| Auth endpoint | 300/min | Frequent polling |

---

## Database

**16 PostgreSQL tables** managed via SQLAlchemy 2.0 + Alembic migrations.

**Core tables:**
- `emails` - Raw email data (headers, body, attachments metadata)
- `cases` - Detection cases (1:1 with emails)
- `analyses` - Pipeline analysis results (heuristics, ML, LLM)
- `evidences` - Supporting evidence for analyses
- `users` - Local user records (synced from Clerk)
- `quarantine_actions` - Quarantine operations history
- `case_notes` - Analyst investigation notes
- `fp_reviews` - False positive reviews
- `alert_events` - Triggered alerts
- `alert_rules` - Alert configuration

**Migrations:**
```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "add new column"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## ML Model

**Model:** DistilBERT (distilbert-base-uncased) fine-tuned for binary classification
**Parameters:** 66M
**Inference time:** ~18ms
**Input:** Email subject + body (max 512 tokens)
**Output:** Phishing probability [0.0, 1.0]

### Training (for ML engineer)

```bash
cd ml

# 1. Prepare dataset
# Place data in ml/data/raw/ (CSV: text, label)

# 2. Process data
python src/preprocess.py

# 3. Train model
python src/train.py

# 4. Evaluate
python src/evaluate.py

# 5. Copy model to backend
cp -r models/distilbert-guardia ../backend/ml_models/
```

**Expected dataset:**
- ~5k-10k labeled emails (phishing/legitimate)
- 80/10/10 train/val/test split
- Balanced classes

**Model location:**
- Training: `ml/models/distilbert-guardia/`
- Inference: `backend/ml_models/distilbert-guardia/`

**Note:** Pipeline works without ML model (graceful degradation: Heuristics 60% + LLM 40%)

---

## Authentication

**Provider:** [Clerk](https://clerk.com)
**Method:** RS256 JWT (asymmetric)
**Access:** Invitation-only (no public signup)

**Roles:**
- `administrator` - Full access (user management, settings)
- `analyst` - Case resolution, quarantine actions
- `auditor` - Read-only access

**Flow:**
1. User logs in via Clerk (frontend)
2. Clerk returns RS256 JWT
3. Frontend sends JWT in `Authorization: Bearer <token>` header
4. Backend verifies JWT with Clerk public PEM key
5. Backend loads local user record (hybrid sync)

**Local user sync:**
- Clerk webhook → `POST /api/v1/auth/sync-user`
- Backend maintains local `users` table for case ownership
- User creation/update synced automatically

---

## Monitoring

### Health Check

```bash
curl https://guardia-backend-xxxxx.run.app/health
```

Response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": true
}
```

### Pipeline Metrics

**Dashboard:** http://localhost:3000/monitoring

**Metrics tracked:**
- LLM: token usage, cost ($), latency (p50/p95/p99), error rate
- ML: inference time, confidence distribution, accuracy
- Heuristics: execution time, triggered rules, score distribution

**Alerts:**
- High-risk detections → Slack webhook
- Pipeline failures → Error logs (structlog JSON)
- Rate limit exceeded → HTTP 429

---

## Testing

### Backend Tests

```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=60

# Run specific test
pytest tests/unit/test_heuristics.py -v

# Run integration tests
pytest tests/integration/ -v
```

**Coverage:** 45% unit, ~20% integration (using mocks)
**Target:** 60%+ for production

### Frontend Tests

```bash
cd frontend

# Unit tests (Vitest)
npm run test -- --run
npm run test -- --coverage

# E2E tests (Playwright)
npm run test:e2e

# Specific test
npm run test -- src/stores/cases.spec.ts
```

**Coverage:** 30%+ target (stores + critical components)

---

## Troubleshooting

### Backend won't start

**macOS/Linux:**
```bash
# Check Python version
python --version  # Must be 3.11+

# Reinstall dependencies
cd backend
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Run migrations
alembic upgrade head
```

**Windows (PowerShell):**
```powershell
# Check Python version
python --version  # Must be 3.11+

# Reinstall dependencies
cd backend
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Run migrations
$env:PYTHONPATH = "."
.venv\Scripts\alembic.exe upgrade head
```

### Frontend build fails

**macOS/Linux:**
```bash
# Clear cache
cd frontend
rm -rf node_modules dist .vite
npm install

# Check Node version
node --version  # Must be 18+
```

**Windows (PowerShell):**
```powershell
# Clear cache
cd frontend
Remove-Item -Recurse -Force node_modules, dist, .vite -ErrorAction SilentlyContinue
npm.cmd install

# Check Node version
node --version  # Must be 18+
```

### Database migration conflicts

```bash
# View current version
alembic current

# Rollback to specific version
alembic downgrade <revision>

# Force to latest
alembic upgrade head
```

### Rate limit errors (HTTP 429)

- Check `RATE_LIMIT_PER_MINUTE` in `.env`
- Default: 1000/min (development), 100/min (production)
- Specific endpoints have lower limits (see Rate Limits section)

---

## Windows

This section covers the full local setup on **Windows with PowerShell**.

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Install from python.org or Microsoft Store |
| Node.js | 18+ | Install from nodejs.org |
| Git | 2.30+ | Install from git-scm.com |
| Docker Desktop | 20+ | Optional — only needed to run local PostgreSQL |

### PowerShell Execution Policy

Many Windows machines have `AllSigned` execution policy, which blocks `.ps1` scripts (including
npm's `npm.ps1` shim and Python's `Activate.ps1`). **Workaround: use `.exe` and `.cmd` binaries directly.**

```powershell
# Check your policy
Get-ExecutionPolicy -List

# If restricted, you can try (may be blocked by GPO):
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

If the policy cannot be changed (e.g. corporate GPO), use the workarounds in the commands below.

### Setup

```powershell
# 1. Clone
git clone https://github.com/your-org/guardia.git
cd guardia

# 2. Backend environment
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Create .env (copy from .env.example and fill in values)
Copy-Item .env.example .env
# Edit backend\.env with your credentials

# 3. Run migrations
$env:PYTHONPATH = "."
.venv\Scripts\alembic.exe upgrade head

# 4. Frontend environment
cd ..\frontend
npm.cmd install                           # Use npm.cmd, not npm, in PowerShell

# Create .env.local
Copy-Item .env.example .env.local
# Edit frontend\.env.local with VITE_API_BASE_URL and VITE_CLERK_PUBLISHABLE_KEY
```

### Start Services

Open **two PowerShell terminals** (or use PowerShell background jobs):

**Terminal 1 — Backend:**
```powershell
cd backend
$env:PYTHONPATH = "."
.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm.cmd run dev
```

**Or using PowerShell background jobs (single terminal):**
```powershell
# Start backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\path\to\guardia\backend"
    $env:PYTHONPATH = "."
    & ".venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 2>&1
}

# Start frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "C:\path\to\guardia\frontend"
    & "npm.cmd" run dev 2>&1
}

# Check output
Start-Sleep -Seconds 5
Receive-Job -Id $backendJob.Id   # Should show "Uvicorn running on http://0.0.0.0:8000"
Receive-Job -Id $frontendJob.Id  # Should show "VITE ready in ... http://localhost:3000/"

# Stop when done
Stop-Job -Id $backendJob.Id, $frontendJob.Id
Remove-Job -Id $backendJob.Id, $frontendJob.Id
```

### Environment Files

| File | Location | Purpose |
|------|----------|---------|
| `backend\.env` | `backend/` | Backend config (DB, Clerk, OpenAI, etc.) |
| `frontend\.env.local` | `frontend/` | Frontend config (API URL, Clerk key) |

**Minimum `backend\.env`:**
```env
APP_ENV=local
APP_DEBUG=true
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
OPENAI_API_KEY=sk-proj-...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Minimum `frontend\.env.local`:**
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### Common Issues on Windows

| Problem | Cause | Fix |
|---------|-------|-----|
| `npm : ... npm.ps1 is not digitally signed` | AllSigned policy | Use `npm.cmd` instead of `npm` |
| `Activate.ps1 cannot be loaded` | AllSigned policy | Use `.venv\Scripts\python.exe` directly |
| `PYTHONPATH` not recognized as env var | Bash syntax in PowerShell | Use `$env:PYTHONPATH = "."` |
| `make dev` fails | GNU Make not installed | Use manual commands above |
| `rm -rf` not found | Bash command | Use `Remove-Item -Recurse -Force` |

### Verify Installation

```powershell
# Backend health
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Select-Object StatusCode, Content
# Expected: 200, {"status":"ok","version":"0.1.0","database":true}

# Frontend
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Select-Object StatusCode
# Expected: 200
```

---

## Contributing

1. Create feature branch from `main`
2. Follow code style guidelines
3. Write tests for new features
4. Ensure `make lint` passes
5. Ensure `make test` passes
6. Create PR to `staging` first
7. After staging approval, merge to `main`

**Commit messages:**
- Brief, one line
- Spanish or English
- No AI/Claude references
- Examples: "add rate limiting", "fix email parser", "mejora dashboard"

---

## License

All rights reserved. Strike Security.

---

## Academic Context

This project is a university thesis (ORT Uruguay) developed for Strike Security. Technical decisions balance production viability with academic rigor.

**Thesis supervisor:** [Name]
**Student:** [Name]
**Year:** 2024-2025

---

<p align="center">
  <sub>Built with Python, Vue, and AI for Strike Security</sub>
</p>
