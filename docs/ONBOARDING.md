# Onboarding Guide

Guía completa de onboarding para nuevos desarrolladores y usuarios del sistema Guard-IA. Incluye setup, workflows, y primeros pasos.

---

## Table of Contents

**Para Desarrolladores:**
1. [Developer Setup](#developer-setup-30-minutos)
2. [Development Workflow](#development-workflow)
3. [First Tasks](#first-tasks)
4. [Resources](#resources-para-developers)

**Para Analistas (Users):**
5. [Analyst User Guide](#analyst-user-guide)
6. [Using the Platform](#using-the-platform)
7. [Common Tasks](#common-tasks)

---

## Developer Setup (30 minutos)

### Prerequisites

**Required:**
- **Git** 2.30+
- **Python** 3.11+ (usar pyenv recomendado)
- **Node.js** 18+ (usar nvm recomendado)
- **Docker** 20+ & Docker Compose
- **Make** (pre-installed en macOS/Linux)

**Optional:**
- **VSCode** o **Cursor** (editores recomendados)
- **Postman** o **Insomnia** (para testear API)
- **TablePlus** o **DBeaver** (DB client)

---

### Step 1: Clone Repository

```bash
# Clone repo
git clone https://github.com/sogliano/guardia.git
cd guardia

# Verificar estructura
ls -la
# Debe tener: backend/, frontend/, ml/, infra/, docs/, .github/
```

---

### Step 2: Configure Environment

**Backend (.env):**
```bash
cd backend
cp .env.example .env

# Editar .env con tus credenciales
# Obtener de 1Password o preguntar a DevOps Lead
nano .env
```

**Variables requeridas:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/guardia

# Clerk (Auth)
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

# OpenAI (LLM)
OPENAI_API_KEY=sk-proj-xxxxx

# Slack (Alerts - opcional en dev)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Environment
ENVIRONMENT=development
```

**Frontend (.env.local):**
```bash
cd ../frontend
cp .env.example .env.local

nano .env.local
```

```bash
# API Backend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Clerk (Auth)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
```

---

### Step 3: Start Services

**Opción 1: Make (recomendado)**
```bash
# Desde raíz del proyecto
make dev

# Esto inicia:
# - PostgreSQL (localhost:5432)
# - MLflow (localhost:5000)
# - Backend (localhost:8000)
# - Frontend (localhost:3000)
# - Gateway SMTP (localhost:2525) - opcional
```

**Opción 2: Manual**
```bash
# Terminal 1: Database
docker-compose up db

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
alembic upgrade head  # Run migrations
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

**Services running:**
- 🐘 PostgreSQL: `localhost:5432`
- 🚀 Backend API: `http://localhost:8000`
- 🎨 Frontend: `http://localhost:3000`
- 📊 MLflow: `http://localhost:5000`
- 📚 API Docs: `http://localhost:8000/docs`

---

### Step 4: Verify Installation

**Backend health check:**
```bash
curl http://localhost:8000/health

# Expected:
# {
#   "status": "healthy",
#   "version": "0.2.0",
#   "timestamp": "2025-02-01T10:00:00Z"
# }
```

**Frontend:**
- Abrir browser: `http://localhost:3000`
- Debe mostrar login screen (Clerk)

**Database:**
```bash
# Connect to DB
psql postgresql://postgres:postgres@localhost:5432/guardia

# List tables
\dt

# Expected: users, emails, cases, analyses, ...
\q
```

---

### Step 5: Run Tests

```bash
# Backend tests
cd backend
pytest

# Expected: All tests pass (puede tardar 30s)

# Frontend tests
cd ../frontend
npm run test

# Expected: All tests pass
```

**Si tests fallan:**
- Verificar que DB está corriendo
- Ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

### Step 6: Create Test User (Optional)

```bash
# Si Clerk no está configurado, crear user manual en DB
psql postgresql://postgres:postgres@localhost:5432/guardia

INSERT INTO users (id, clerk_id, email, role, name)
VALUES (
    gen_random_uuid(),
    'user_test123',
    'test@strike.sh',
    'analyst',
    'Test User'
);
\q
```

---

## Development Workflow

### 1. Pick a Task

**GitHub Issues:**
- Ir a https://github.com/sogliano/guardia/issues
- Filtrar por label: `good first issue` (para nuevos developers)
- Asignarte el issue

**Jira (si usa Strike Security):**
- Board: https://strike-security.atlassian.net/
- Pick task de backlog

---

### 2. Create Feature Branch

```bash
# Crear branch desde main
git checkout main
git pull origin main

# Branch naming convention:
# - feat/feature-name     (nueva feature)
# - fix/bug-name         (bug fix)
# - docs/doc-name        (documentación)
# - refactor/what        (refactoring)

git checkout -b feat/add-email-filters

# Ejemplo de nombres válidos:
# - feat/rate-limiting-quarantine
# - fix/pipeline-timeout
# - docs/update-api-reference
```

---

### 3. Write Code

**Seguir standards en [CLAUDE.md](../CLAUDE.md):**

**Backend (Python):**
- Indent: 4 spaces
- Type hints completos
- Async/await
- Structlog logging
- Tests (coverage ≥60%)

**Frontend (Vue/TypeScript):**
- Indent: 2 spaces
- `<script setup lang="ts">`
- Pinia stores
- Type interfaces
- Tests (coverage ≥30%)

**Example commit flow:**
```bash
# Work on code
nano backend/app/api/v1/cases.py

# Run linter
make lint

# Run tests
make test

# Add files
git add backend/app/api/v1/cases.py
git add backend/tests/integration/test_api_cases.py

# Commit (brief, one line, Spanish or English)
git commit -m "add status filter to cases endpoint"

# NO mencionar "Claude" o "AI" en commit message
```

---

### 4. Create Pull Request

```bash
# Push branch
git push origin feat/add-email-filters

# Crear PR en GitHub:
# - Base: staging (no main directamente)
# - Title: Brief description
# - Description: What changed, why, how to test
# - Reviewers: Assign team lead
```

**PR Template:**
```markdown
## Description
Add status filter to GET /cases endpoint to filter by case status.

## Changes
- Added `status` query param to CasesService.list_cases()
- Added test coverage for status filter
- Updated API_DOCUMENTATION.md

## Testing
1. Start backend: `make dev`
2. Test: `curl "localhost:8000/api/v1/cases?status=quarantined"`
3. Verify: Returns only quarantined cases

## Screenshots
[Si aplica]

## Checklist
- [x] Tests written and passing
- [x] Linting passes
- [x] Documentation updated
- [x] No console.log or debug prints
```

---

### 5. Code Review

**Esperando review:**
- Reviewer deja comentarios
- Hacer cambios solicitados
- Push nuevos commits (no force push)

**Checklist para PR approval:**
- [ ] Code follows CLAUDE.md standards
- [ ] Tests written and passing (≥60% backend, ≥30% frontend)
- [ ] Linting passes (ruff, mypy, eslint)
- [ ] No console.log or debug prints
- [ ] No secrets hardcoded
- [ ] Documentation updated (si es necesario)
- [ ] PR description explains changes

---

### 6. Merge & Deploy

**After approval:**
1. Merge PR to `staging` branch
2. GitHub Action auto-deploys to staging
3. Test en staging environment
4. Si todo OK, merge `staging` → `main`
5. GitHub Action auto-deploys to production

**NO hacer:**
- ❌ Merge directamente a `main`
- ❌ Push sin PR
- ❌ Force push a `main` o `staging`

---

## First Tasks

### Task 1: Read Documentation (30 min)

**Orden recomendado:**
1. [README.md](../README.md) - Overview general
2. [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura completa
3. [CLAUDE.md](../CLAUDE.md) - Coding standards
4. [TESTING.md](./TESTING.md) - Cómo escribir tests
5. Este documento (ONBOARDING.md)

---

### Task 2: Run Pipeline Locally (15 min)

**Objetivo:** Entender el pipeline de detección.

```bash
# 1. Start services
make dev

# 2. Simulate email (desde otro terminal)
cd backend
python scripts/simulate_email.py

# 3. Ver logs del pipeline
docker logs -f guardia-backend | grep "pipeline"

# Expected output:
# pipeline_started email_id=... case_id=...
# heuristics_completed score=0.65
# ml_completed score=0.82
# llm_completed score=0.78
# pipeline_completed final_score=0.75
```

**Explorar en frontend:**
- Abrir `localhost:3000`
- Login (Clerk)
- Ir a Cases → Ver caso recién creado
- Explorar Dashboard, Email Explorer

---

### Task 3: Pick "Good First Issue" (2-4 horas)

**Filtrar issues:**
- GitHub → Issues → Label: `good first issue`

**Ejemplos de good first issues:**
- Add loading spinner to Dashboard
- Fix typo in API documentation
- Add unit test for heuristics function
- Improve error message en login screen

**Steps:**
1. Assign issue a ti mismo
2. Create feature branch
3. Write code + tests
4. Create PR
5. Esperar review

---

## Resources para Developers

### Documentation

| Documento | Qué cubre |
|-----------|-----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Arquitectura, stack, componentes, ERD |
| [CLAUDE.md](../CLAUDE.md) | Coding standards, patterns, naming |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | Referencia completa de API REST |
| [TESTING.md](./TESTING.md) | Estrategia de testing, ejemplos |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Problemas comunes y soluciones |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Cómo deployar a staging/production |
| [DATABASE_MAINTENANCE.md](./DATABASE_MAINTENANCE.md) | Migrations, indexes, backups |
| [ML_TRAINING_GUIDE.md](./ML_TRAINING_GUIDE.md) | Cómo entrenar modelo ML |
| [RUNBOOK.md](./RUNBOOK.md) | Incident response, rollbacks |

---

### Makefile Commands

```bash
make dev              # Start all services (db, mlflow, backend, frontend)
make test             # Run all tests (backend + frontend)
make lint             # Run linting (ruff + mypy + eslint)
make migrate          # Run Alembic migrations
make migration msg="" # Create new migration
make train-ml         # Train ML model
make simulate-email   # Send test email al pipeline
```

Ver `Makefile` para todos los comandos disponibles.

---

### Slack Channels

| Canal | Propósito |
|-------|-----------|
| **#guardia-dev** | General development, preguntas técnicas |
| **#guardia-backend** | Backend-specific (Python, API, DB) |
| **#guardia-frontend** | Frontend-specific (Vue, TypeScript) |
| **#guardia-ml** | ML model, training, evaluation |
| **#guardia-infra** | DevOps, deployment, monitoring |
| **#guardia-alerts** | Production alerts (Slack webhooks) |

---

### Useful Tools

**Editors:**
- VSCode con extensions: Python, Volar (Vue), Prettier, ESLint
- Cursor (AI-powered code editor)

**API Testing:**
- Postman: https://www.postman.com/
- Insomnia: https://insomnia.rest/
- HTTPie: `brew install httpie`

**Database Clients:**
- TablePlus: https://tableplus.com/
- DBeaver: https://dbeaver.io/
- psql CLI

---

## Analyst User Guide

### Accessing the Dashboard

**URL:** https://guardia.strike.sh (production)

**Login:**
1. Navigate to https://guardia.strike.sh
2. Click "Sign In"
3. Use Clerk SSO (email + password o Google)
4. First-time: Request invitation from Administrator

**Roles:**
- **Analyst:** View cases, resolve cases, access dashboard
- **Administrator:** All analyst permissions + user management

---

## Using the Platform

### Dashboard Overview

**URL:** `/dashboard`

**Widgets:**
1. **Total Emails:** Count de emails procesados (período seleccionado)
2. **Quarantined:** Count de casos en cuarentena
3. **Average Score:** Promedio de final_score (0-1)
4. **Detection Rate:** % de emails detectados como phishing
5. **Trend Chart:** Timeline de detecciones
6. **Top Threats:** Senders más peligrosos

**Filters:**
- **Date Range:** Last 24h, Last 7 days, Last 30 days, Custom
- **Refresh:** Auto-refresh cada 30s (toggle)

---

### Email Explorer

**URL:** `/emails`

**Features:**
- **List view:** Tabla de emails con sender, recipient, subject, received_at
- **Search:** Buscar en sender, recipient, subject, body
- **Filters:**
  - Date range
  - Sender
  - Recipient
  - Has case (yes/no)
- **Pagination:** 20 items per page

**Actions:**
- Click email → Ver detalle (headers, body, attachments)
- Si tiene caso → Link a caso

---

### Cases

**URL:** `/cases`

**Features:**
- **List view:** Tabla de casos con status, risk_level, final_score, created_at
- **Search:** Buscar en email sender/subject
- **Filters:**
  - Status: pending, analyzing, quarantined, resolved
  - Risk level: low, medium, high, critical
  - Verdict: allowed, warned, quarantined, blocked
  - Date range
- **Sort:** By date, score, risk_level

**Case Detail:**
- Email content (sender, subject, body)
- Pipeline analysis:
  - Heuristics: score + evidences
  - ML: score + model version
  - LLM: score + explanation
- Final score & verdict
- Actions: Resolve, Quarantine, Release (si quarantined)

---

### Quarantine

**URL:** `/quarantine`

**Features:**
- Lista de casos en cuarentena
- Filters: risk_level, date range
- Sort: By score, date

**Actions:**
1. **Release:** Liberar email (envía a destinatario)
2. **Keep Quarantined:** Confirmar bloqueo
3. **Add to Allowlist:** Agregar sender a whitelist (no implementado aún)

---

## Common Tasks

### Task 1: Resolve a Case

**Scenario:** Revisar caso y tomar decisión final.

**Steps:**
1. Go to **Cases** tab
2. Click on case para ver detalle
3. Review:
   - Email content
   - Heuristics evidences (domain mismatch, urgency keywords, etc.)
   - ML score (confidence)
   - LLM explanation
4. Click **"Resolve"** button
5. Select verdict:
   - **Allowed:** Email es legítimo (false positive)
   - **Warned:** Email sospechoso pero no crítico
   - **Quarantined:** Email peligroso, mantener bloqueado
   - **Blocked:** Email malicioso confirmado
6. Add notes (opcional): "False positive - verified with sender"
7. Click **"Confirm"**

**Result:** Case status cambia a `resolved`, email se entrega (si verdict=allowed) o queda bloqueado.

---

### Task 2: Release Quarantined Email

**Scenario:** Email en cuarentena es falso positivo, necesitas liberarlo.

**Steps:**
1. Go to **Quarantine** tab
2. Find email (usar filters si es necesario)
3. Click on case
4. Review analysis (verificar que es legítimo)
5. Click **"Release"** button
6. Add notes: "Verified with recipient - legitimate email"
7. Click **"Confirm"**

**Result:** Email se envía a destinatario, case status → `resolved`, verdict → `allowed`.

---

### Task 3: Search for Phishing Pattern

**Scenario:** Detectaste nuevo patrón de phishing, quieres buscar casos similares.

**Steps:**
1. Go to **Cases** tab
2. Use **Search** box:
   - Ejemplo: "urgent account verification"
3. Apply filters:
   - Risk level: high, critical
   - Status: quarantined
4. Review results
5. Bulk action (si está disponible): Resolve all as `blocked`

---

### Task 4: Generate Report

**Scenario:** Necesitas report de detecciones última semana para management.

**Steps:**
1. Go to **Dashboard**
2. Select date range: **Last 7 days**
3. Tomar screenshot de widgets
4. Go to **Cases** → Export CSV (si está disponible)
5. Análisis en Excel:
   - Top senders
   - Detection rate
   - False positive rate

**Future feature:** Auto-generated PDF report (no implementado aún).

---

## FAQs

### Q: ¿Qué hago si backend no inicia?

**A:** Ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#backend-wont-start)

---

### Q: ¿Cómo agrego un nuevo endpoint a la API?

**A:**
1. Create endpoint en `backend/app/api/v1/`
2. Add service logic en `backend/app/services/`
3. Add tests en `backend/tests/integration/`
4. Update [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
5. Create PR

Ver [CLAUDE.md](../CLAUDE.md#backend-patterns) para patrones.

---

### Q: ¿Cómo entreno un nuevo modelo ML?

**A:** Ver [ML_TRAINING_GUIDE.md](./ML_TRAINING_GUIDE.md)

---

### Q: ¿Cómo hago rollback de un deployment malo?

**A:** Ver [RUNBOOK.md](./RUNBOOK.md#rollback-procedures)

---

### Q: ¿Dónde están los logs de producción?

**A:**
- **Backend (Cloud Run):** GCP Console → Cloud Run → guardia-backend → Logs
- **Frontend (Vercel):** Vercel Dashboard → Project → Deployments → Logs
- **Database (Neon):** Neon Console → Project → Monitoring

---

### Q: ¿Cómo reporto un bug?

**A:**
1. Check si ya existe issue en GitHub
2. Si no, crear issue:
   - Title: Brief description
   - Description: Steps to reproduce, expected vs actual, screenshots
   - Labels: `bug`, `priority-high` (si es crítico)
3. Asignar a team lead si es urgente

---

## Next Steps

**Para Developers:**
1. ✅ Complete setup (30 min)
2. ✅ Read documentation (1 hora)
3. ✅ Run pipeline locally (15 min)
4. ✅ Pick first issue (2-4 horas)
5. ⏳ Submit first PR
6. ⏳ Join daily standup (Slack #guardia-dev)

**Para Analysts:**
1. ✅ Access dashboard (first login)
2. ✅ Explore Cases tab
3. ✅ Resolve first case
4. ⏳ Weekly review de quarantine queue
5. ⏳ Monthly report de detecciones

---

## Feedback

¿Problemas con onboarding? ¿Falta algo en esta guía?

**Contact:**
- Slack: #guardia-dev
- Email: dev@strike.sh
- GitHub Issues: https://github.com/sogliano/guardia/issues

**Improve this doc:**
- Create PR con tus sugerencias
- File issue con label `documentation`
