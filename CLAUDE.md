# Guard-IA

AI-powered pre-delivery email fraud detection middleware (phishing, BEC, impersonation). University thesis (ORT Uruguay) for Strike Security. Single-tenant, Google Workspace integration.

## Architecture

```
guardia/
├── backend/    → Python 3.11 / FastAPI / SQLAlchemy async / PostgreSQL 16
├── frontend/   → Vue 3 / TypeScript / Pinia / Chart.js / Vite
├── ml/         → DistilBERT fine-tuned (66M params) / MLflow
└── infra/      → Docker / Nginx / GCP
```

**Pipeline:** Heuristics (~5ms) → DistilBERT ML (~18ms) → LLM Explainer (2-3s, Claude/GPT-4.1 fallback). LLM explains only, never decides.

**Thresholds:** ALLOW < 0.3, WARN 0.3-0.6, QUARANTINE ≥ 0.8

## Key Paths

- `backend/app/services/pipeline/` — orchestrator, heuristics, ml_classifier, llm_explainer
- `backend/app/models/` — email, case, analysis, alert_event, fp_review
- `backend/app/api/v1/` — REST endpoints
- `backend/app/schemas/` — Pydantic v2 request/response models
- `frontend/src/views/` — page-level Vue components
- `frontend/src/components/` — reusable UI components
- `frontend/src/stores/` — Pinia state management
- `frontend/src/services/` — Axios API clients (base: `services/api.ts`)
- `frontend/src/types/` — TypeScript interfaces

## Coding Rules

### Python (backend/)
- Indent 4 spaces, line length 100
- Lint: `ruff check` (E, F, I, N, W). Types: `mypy`
- All async: SQLAlchemy async, asyncpg, httpx
- Pydantic v2 schemas, structlog logging
- Tests: `pytest` + `pytest-asyncio` (asyncio_mode=auto)

### TypeScript/Vue (frontend/)
- `<script setup lang="ts">`, indent 2 spaces
- Pinia stores, Axios HTTP, Chart.js via vue-chartjs
- Path alias: `@/` → `src/`

### General
- Imports always at top, never mid-code
- LF endings, UTF-8, trim trailing whitespace, final newline
- No emojis in code unless requested

## Commands

```bash
make dev              # Start all (db, mlflow, backend, frontend)
make test             # All tests
make lint             # ruff + mypy + eslint
make migrate          # Run migrations
make migration msg="" # Create migration
```

**URLs:** Backend `localhost:8000/api/v1`, Frontend `localhost:3000`, DB `localhost:5432`

## Git

- Commits: one line, brief, Spanish or English
- No AI/Claude references in commits
- Never auto-push, developer pushes manually
- Feature branches off main

## Design Decisions

- Single-tenant (Strike Security only)
- Clerk auth (RS256 JWT, invitation-only, hybrid sync with local users)
- Pre-delivery interception, not post-delivery scanning
- PostgreSQL JSONB for email metadata
- Thesis project: decisions must balance production viability with academic rigor
