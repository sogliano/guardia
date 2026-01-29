# Guard-IA — Contexto Completo del Proyecto

Documento para usar como contexto al iniciar un nuevo chat de Claude Code.

**Fecha**: Enero 2026
**Estado**: ~20% implementado — infraestructura y auth listos, logica de negocio pendiente

---

## Que es Guard-IA

Middleware de deteccion de fraude en emails corporativos (phishing, BEC, suplantacion) usando IA. Tesis universitaria (ORT Uruguay) para Strike Security. Single-tenant, integrado con Google Workspace, intercepcion pre-delivery.

**Pipeline de 3 etapas secuenciales:**
1. **Heuristic Rules** (~5ms) — SPF/DKIM/DMARC, reputacion de dominio, URLs, patrones de urgencia
2. **DistilBERT Classifier** (~18ms) — `distilbert-base-uncased` fine-tuned, 66M params
3. **LLM Explainer** (2-3s) — Claude Opus 4.5 primary, GPT-4.1 fallback. Solo explica, NO decide.

**Thresholds:** ALLOW < 0.3 | WARN 0.3-0.6 | QUARANTINE 0.6-0.8 | BLOCK >= 0.8

---

## Estructura del Monorepo

```
guardia/
├── backend/        → Python 3.13 / FastAPI / SQLAlchemy async / PostgreSQL 15
├── frontend/       → Vue 3 / TypeScript / PrimeVue 4 / Pinia / Vite
├── ml/             → DistilBERT fine-tuned / MLflow
├── infra/          → Docker / Nginx / GCP configs
├── docs/           → Documentacion del proyecto
└── .env            → Variables de entorno (NO commitear)
```

---

## Estado de Implementacion

### Implementado (funcional)
- Todos los modelos de base de datos con migracion aplicada
- Todos los schemas Pydantic
- Auth completo con Clerk (JWT RS256, JIT provisioning, hybrid sync)
- Frontend: Login con Clerk modal, Dashboard template, Layout, Router
- Axios interceptor async con Clerk getToken
- Pinia auth store funcional
- Endpoint `GET /auth/me` funcional
- DB PostgreSQL 15 local con todas las tablas creadas

### Stubs (estructura sin logica)
- Todos los services: case, email, dashboard, alert, notification, policy, quarantine, report
- Todos los endpoints API (devuelven `raise NotImplementedError`)
- Pipeline: orchestrator, heuristics, ml_classifier, llm_explainer
- Frontend views: Cases, Quarantine, Emails, Policies, Alerts, Reports, Settings
- Frontend stores: cases, dashboard, quarantine, notifications, settings

---

## Modelos de Base de Datos

### users
```
id              UUID PK
clerk_id        VARCHAR(255) UNIQUE INDEX — identificador de Clerk
email           VARCHAR(255) UNIQUE
password_hash   VARCHAR(255) NULLABLE — legacy, no se usa con Clerk
full_name       VARCHAR(255)
role            VARCHAR(20) DEFAULT 'analyst' — administrator | analyst | auditor
is_active       BOOLEAN DEFAULT true
last_login_at   TIMESTAMPTZ NULLABLE
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

### email_artifacts
```
id              UUID PK
message_id      VARCHAR UNIQUE — ID del email original
sender_email    VARCHAR
sender_name     VARCHAR NULLABLE
recipient_email VARCHAR
subject         VARCHAR NULLABLE
body_text       TEXT NULLABLE
body_html       TEXT NULLABLE
headers         JSONB — headers del email
urls            JSONB — URLs extraidas
attachments     JSONB — metadata de adjuntos
received_at     TIMESTAMPTZ NULLABLE
ingested_at     TIMESTAMPTZ NULLABLE
created_at      TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```
Relaciones: `case` (one-to-one)

### cases
```
id                UUID PK
email_artifact_id UUID FK → email_artifacts.id
status            VARCHAR DEFAULT 'pending' — pending | analyzing | analyzed | resolved
final_score       FLOAT NULLABLE
risk_level        VARCHAR NULLABLE — allow | warn | quarantine | block
action            VARCHAR NULLABLE — allowed | warned | quarantined | blocked
resolved_by       UUID NULLABLE FK → users.id
resolved_at       TIMESTAMPTZ NULLABLE
created_at        TIMESTAMPTZ
updated_at        TIMESTAMPTZ
```
Relaciones: `email_artifact` (one-to-one), `decisions` (one-to-many), `resolver` (FK user)

### decisions
```
id                UUID PK
case_id           UUID FK → cases.id
stage             VARCHAR — heuristic | ml | llm | final
score             FLOAT NULLABLE
reasoning         TEXT NULLABLE — explicacion del LLM
metadata_         JSONB (column name: metadata)
execution_time_ms INTEGER NULLABLE
created_at        TIMESTAMPTZ DEFAULT now()
```
Relaciones: `case` (many-to-one), `evidences` (one-to-many)

### evidences
```
id            UUID PK
decision_id   UUID FK → decisions.id
type          VARCHAR — domain_spoofing, url_shortener, keyword_urgency, auth_spf_fail, etc.
severity      VARCHAR — low | medium | high | critical
description   VARCHAR
raw_data      JSONB
created_at    TIMESTAMPTZ DEFAULT now()
```

### policies
```
id          UUID PK
name        VARCHAR
description VARCHAR NULLABLE
category    VARCHAR — domain | url | keyword | auth
rules       JSONB
is_active   BOOLEAN DEFAULT true
created_by  UUID NULLABLE FK → users.id
created_at  TIMESTAMPTZ
updated_at  TIMESTAMPTZ
```

### alerts
```
id        UUID PK
case_id   UUID NULLABLE FK → cases.id
type      VARCHAR
severity  VARCHAR — low | medium | high | critical
title     VARCHAR
message   VARCHAR NULLABLE
is_read   BOOLEAN DEFAULT false
created_at TIMESTAMPTZ DEFAULT now()
```

### notifications
```
id        UUID PK
user_id   UUID FK → users.id
type      VARCHAR
title     VARCHAR
message   VARCHAR NULLABLE
is_read   BOOLEAN DEFAULT false
metadata_ JSONB (column name: metadata)
created_at TIMESTAMPTZ DEFAULT now()
```

---

## Enums y Constantes (`backend/app/core/constants.py`)

```python
CaseStatus:    pending | analyzing | analyzed | resolved
RiskLevel:     allow | warn | quarantine | block
CaseAction:    allowed | warned | quarantined | blocked
PipelineStage: heuristic | ml | llm | final
UserRole:      administrator | analyst | auditor
PolicyCategory: domain | url | keyword | auth
Severity:      low | medium | high | critical

EvidenceType: domain_spoofing, domain_typosquatting, domain_blacklisted,
              domain_suspicious_tld, url_shortener, url_ip_based, url_mismatch,
              url_suspicious, keyword_urgency, keyword_phishing, keyword_caps_abuse,
              auth_spf_fail, auth_dkim_fail, auth_dmarc_fail, ml_high_score

Heuristic weights: domain=0.25, url=0.25, keyword=0.25, auth=0.25
```

---

## API Endpoints (`/api/v1`)

| Metodo | Ruta | Estado | Descripcion |
|--------|------|--------|-------------|
| GET | `/auth/me` | HECHO | Perfil del usuario autenticado |
| POST | `/emails/ingest` | STUB | Ingestar email, crear caso, triggear pipeline |
| GET | `/emails` | STUB | Listar emails con paginacion |
| GET | `/emails/{id}` | STUB | Detalle de email |
| GET | `/cases` | STUB | Listar casos con filtros y paginacion |
| GET | `/cases/{id}` | STUB | Caso con decisions y evidences |
| POST | `/cases/{id}/resolve` | STUB | Resolver caso |
| GET | `/dashboard` | STUB | Stats, graficos, tendencias |
| GET | `/quarantine` | STUB | Emails en cuarentena |
| POST | `/quarantine/{id}/action` | STUB | Aprobar/rechazar cuarentena |
| GET | `/policies` | STUB | Listar politicas |
| POST | `/policies` | STUB | Crear politica |
| GET | `/policies/{id}` | STUB | Detalle de politica |
| PUT | `/policies/{id}` | STUB | Actualizar politica |
| DELETE | `/policies/{id}` | STUB | Eliminar politica |
| GET | `/alerts` | STUB | Listar alertas |
| PUT | `/alerts/{id}/read` | STUB | Marcar como leida |
| GET | `/notifications` | STUB | Notificaciones del usuario |
| PUT | `/notifications/{id}/read` | STUB | Marcar como leida |
| POST | `/reports/export` | STUB | Exportar CSV/PDF |
| GET | `/settings` | PARCIAL | Thresholds del pipeline |
| PUT | `/settings` | STUB | Actualizar settings |

Todos los endpoints protegidos con `CurrentUser` (Clerk JWT).

---

## Schemas Pydantic (backend/app/schemas/)

```
user.py:         UserCreate(clerk_id, email, full_name, role)
                 UserResponse(id, clerk_id, email, full_name, role, is_active, last_login_at, created_at)

email.py:        EmailIngest(message_id, sender_email, sender_name, recipient_email, subject, body_text, body_html, headers, urls, attachments, received_at)
                 EmailResponse(id, message_id, sender_email, sender_name, recipient_email, subject, body_text, headers, urls, received_at, ingested_at, created_at)

case.py:         CaseResponse(id, email_artifact_id, status, final_score, risk_level, action, resolved_by, resolved_at, created_at, updated_at)
                 CaseList(items[], total, page, size)
                 CaseResolve(action)

decision.py:     DecisionResponse(id, case_id, stage, score, reasoning, metadata, execution_time_ms, created_at)

evidence.py:     EvidenceResponse(id, decision_id, type, severity, description, raw_data, created_at)

policy.py:       PolicyCreate(name, description, category, rules, is_active)
                 PolicyUpdate(name?, description?, category?, rules?, is_active?)
                 PolicyResponse(id, name, description, category, rules, is_active, created_by, created_at, updated_at)

alert.py:        AlertResponse(id, case_id, type, severity, title, message, is_read, created_at)

notification.py: NotificationResponse(id, user_id, type, title, message, is_read, metadata, created_at)

dashboard.py:    DashboardStats(total_emails_analyzed, emails_today, blocked_count, quarantined_count, warned_count, allowed_count, avg_score, pending_cases)
                 ChartDataPoint(label, value)
                 DashboardResponse(stats, risk_distribution[], daily_trend[])

quarantine.py:   QuarantineAction(action: approve|reject, reason?)

report.py:       ReportFilter(date_from?, date_to?, risk_level?, status?)
                 ReportExport(format: csv|pdf, filters)
```

---

## Auth (Clerk — Implementado)

**Flujo:**
1. Frontend: `@clerk/vue` plugin con `clerkPlugin` en `main.ts`
2. `App.vue`: watch `isLoaded`/`isSignedIn` → redirect automatico login/dashboard
3. `setClerkGetToken()` bridge → axios interceptor agrega `Bearer` token
4. Backend: `HTTPBearer` extrae token → `verify_clerk_token()` con PyJWT RS256 → busca user por `clerk_id`
5. JIT Provisioning: si user no existe localmente, `sync_clerk_user()` lo crea via Clerk Backend API
6. `CurrentUser` dependency inyecta el `User` en cada endpoint

**Archivos clave:**
- `backend/app/core/security.py` — `verify_clerk_token()` (PyJWT RS256)
- `backend/app/api/deps.py` — `get_current_user()`, `CurrentUser`
- `backend/app/services/user_sync_service.py` — JIT provisioning desde Clerk API
- `backend/app/api/middleware/auth.py` — `get_bearer_token()` (HTTPBearer)
- `frontend/src/App.vue` — auth orchestrator
- `frontend/src/services/api.ts` — `setClerkGetToken()` + async interceptor
- `frontend/src/stores/auth.ts` — `fetchProfile()` / `clearProfile()`

**Clerk Dashboard:**
- App: `secure-terrapin-50`
- Frontend URL: `https://secure-terrapin-50.clerk.accounts.dev`
- User de test creado: `test@test.com` / `test123`
- Login funcional con Google (nsoglianosuarez@gmail.com verificado)

---

## Frontend Architecture

**Stack:** Vue 3 + TypeScript + PrimeVue 4 + Pinia + Vite + Axios + Chart.js

**Entry points:**
- `main.ts` — createApp, plugins (Pinia, Clerk, Router, PrimeVue/Aura)
- `App.vue` — auth orchestrator con Clerk watch
- `router/index.ts` — sin guards (App.vue maneja redirect)

**Layout:** `AppLayout.vue` contiene `AppSidebar.vue` + `AppTopbar.vue` + `<RouterView>`
- Sidebar: logo, nav items, `<UserButton>` de Clerk en footer
- Topbar: page title, search box placeholder, notifications icon, user avatar (Clerk image)

**Views existentes (todas stub excepto Login y Dashboard template):**
LoginView, DashboardView, CasesView, CaseDetailView, QuarantineView,
EmailExplorerView, PoliciesView, AlertsView, ReportsView, SettingsView,
FPReviewView, NotificationsView

**Stores Pinia:**
- `auth.ts` — FUNCIONAL (fetchProfile, clearProfile, isAuthenticated)
- `cases.ts` — STUB (cases[], total, page, size, loading, filters)
- `dashboard.ts` — STUB (data, loading)
- `quarantine.ts` — STUB (items[], loading)
- `notifications.ts` — STUB
- `settings.ts` — STUB

**Services:**
- `api.ts` — FUNCIONAL (axios + Clerk interceptor)
- `authService.ts` — FUNCIONAL (fetchCurrentUser)
- `caseService.ts` — FUNCIONAL (fetchCases, fetchCase, resolveCase)
- Resto — STUBS

**Types:** `auth.ts`, `case.ts`, `api.ts`, `dashboard.ts`, `policy.ts`, `email.ts`

---

## Configuracion

**Backend config** (`backend/app/config.py` + `.env`):
```
APP_ENV, APP_DEBUG, APP_SECRET_KEY
DATABASE_URL = postgresql+asyncpg://guardia:guardia_dev@localhost:5432/guardia
CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, CLERK_PEM_PUBLIC_KEY
THRESHOLD_ALLOW=0.3, THRESHOLD_WARN=0.6, THRESHOLD_QUARANTINE=0.8
ANTHROPIC_API_KEY, ANTHROPIC_MODEL=claude-opus-4-5-20251101
OPENAI_API_KEY, OPENAI_MODEL=gpt-4.1
ML_MODEL_PATH=./ml_models/distilbert-guardia, ML_MAX_SEQ_LENGTH=256
MLFLOW_TRACKING_URI=http://localhost:5000
```

**Frontend:** `VITE_API_BASE_URL`, `VITE_CLERK_PUBLISHABLE_KEY` en `frontend/.env.local`

**Virtualenv:** `backend/.venv` (Python 3.13 via `/opt/homebrew/bin/python3.13`)

---

## Como Levantar

**Terminal 1 — Backend:**
```bash
cd ~/Desktop/git-repo/guardia/backend
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd ~/Desktop/git-repo/guardia/frontend
npm run dev
```

PostgreSQL 15 corre como servicio de Homebrew (`brew services start postgresql@15`).
Frontend en `http://localhost:3000`, backend en `http://localhost:8000`.

---

## Convenciones de Codigo

**Python:** 3.11+, indent 4, ruff (E,F,I,N,W), mypy, line 100, async everywhere, structlog, imports siempre arriba
**TypeScript/Vue:** Composition API `<script setup lang="ts">`, indent 2, Pinia, Axios, PrimeVue 4
**General:** LF, UTF-8, trim trailing whitespace, final newline
**Git:** commits breves una linea, sin referencias a Claude/AI, NO auto-push

---

## Proximo Paso Sugerido

Implementar la logica de negocio de los services y endpoints. Orden recomendado:
1. `email_service.py` + `POST /emails/ingest` — punto de entrada del pipeline
2. `case_service.py` + endpoints de cases — core del negocio
3. Pipeline: `orchestrator.py` → `heuristics.py` → `ml_classifier.py` → `llm_explainer.py`
4. `dashboard_service.py` — queries de agregacion
5. `quarantine_service.py` — acciones sobre emails en cuarentena
6. Resto de services (alerts, notifications, policies, reports)
7. Frontend: conectar stores y views a los endpoints funcionales
