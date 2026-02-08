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

**Pipeline:** Heuristics (~5ms) → DistilBERT ML (~18ms) → LLM Explainer (2-3s, OpenAI GPT). Final score = weighted average with LLM floor/cap adjustments.

**Thresholds:** ALLOW < 0.3, WARN 0.3-0.6, QUARANTINE 0.6-0.8, BLOCKED ≥ 0.8

## Key Paths

```
backend/app/
├── api/v1/              # REST endpoints (cases, emails, dashboard, monitoring)
├── services/            # Business logic + detection pipeline
│   ├── pipeline/        # orchestrator, heuristics, ml_classifier, llm_explainer
│   ├── case_service.py
│   ├── email_service.py
│   └── ...
├── models/              # SQLAlchemy ORM (16 tables: email, case, analysis, alert_event, etc.)
├── schemas/             # Pydantic v2 request/response (CreateRequest, Response, DetailResponse)
├── core/                # Constants, security, exceptions, rate_limit
├── db/                  # Session + Alembic migrations
└── gateway/             # SMTP server (aiosmtpd) + email parser (RFC 5322)

frontend/src/
├── views/               # Page components (7 views: Dashboard, Cases, EmailExplorer, etc.)
├── components/          # Reusable UI (common: FormInput, ErrorState, LoadingState; dashboard; cases)
├── stores/              # Pinia state (7 stores: cases, dashboard, emails, etc.)
├── services/            # Axios API clients (base: services/api.ts)
├── types/               # TypeScript interfaces (case.ts, email.ts, api.ts, etc.)
└── composables/         # useAuth, useFilters, usePolling

ml/
├── src/                 # train.py, evaluate.py, preprocess.py
├── data/                # raw/, processed/, splits/ (train/val/test)
└── models/              # distilbert-guardia/ (trained model)
```

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

## Backend Patterns

### REST Endpoint Structure

```python
from fastapi import APIRouter, Query, Request
from app.api.deps import CurrentUser, DbSession, RequireAnalyst
from app.core.rate_limit import limiter
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=ListResponse)
@limiter.limit("60/minute")
async def list_resources(
    request: Request,  # Required for rate limiting (slowapi)
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List resources with pagination."""
    svc = ResourceService(db)
    result = await svc.list_resources(page=page, size=size)
    return result
```

**Conventions:**
- Rate limit decorator above `@router` decorator
- `Request` as first parameter (required by slowapi for rate limiting)
- Dependencies: `CurrentUser`, `DbSession`, `RequireAnalyst` (typed, from `app.api.deps`)
- `response_model` always specified (Pydantic schema)
- Error handling: `raise NotFoundError("message")` (custom exceptions)
- `await db.commit()` in mutating endpoints (POST, PUT, DELETE)

### Service Layer Pattern

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.resource import Resource

class ResourceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_resources(self, page: int, size: int) -> dict:
        """List with pagination."""
        query = select(Resource).options(selectinload(Resource.relation))

        # Count subquery
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Pagination
        offset = (page - 1) * size
        query = query.order_by(Resource.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "size": size}

    async def get_resource(self, resource_id: UUID) -> Resource:
        """Get single resource."""
        query = select(Resource).where(Resource.id == resource_id)
        result = await self.db.execute(query)
        resource = result.scalar_one_or_none()

        if not resource:
            raise NotFoundError("Resource not found")

        return resource

    async def create_resource(self, name: str) -> Resource:
        """Create resource."""
        resource = Resource(name=name)
        self.db.add(resource)
        await self.db.flush()  # Get ID before returning
        await self.db.refresh(resource)
        return resource
```

**Conventions:**
- Constructor: `__init__(self, db: AsyncSession)`
- Type hints completos: `async def ... -> Type | None`
- **No usar `commit()` en services** (solo en endpoints)
- `flush()` para obtener IDs antes de retornar
- Eager loading: `selectinload()` para relaciones (evita N+1)
- Raise custom exceptions: `NotFoundError`, `ForbiddenError`, `PipelineError`

### Pydantic Schemas (v2)

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ResourceResponse(BaseModel):
    id: UUID
    name: str
    count: int
    created_at: datetime

    model_config = {"from_attributes": True}  # ORM mode (Pydantic v2)

class ResourceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ResourceDetailResponse(ResourceResponse):
    """Extended response with relations."""
    relation: "RelatedResponse | None" = None
```

**Conventions:**
- `BaseModel` from Pydantic v2
- `model_config = {"from_attributes": True}` for ORM→Pydantic conversion
- Union types: `field: Type | None` (not `Optional[Type]`)
- Separate schemas: `Response`, `DetailResponse`, `CreateRequest`, `UpdateRequest`
- Field validation: `Field(...)` with constraints (min_length, max_length, ge, le)

### SQLAlchemy Models (async)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Index
from app.models.base import UUIDMixin, TimestampMixin, Base

class Resource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

    # Foreign key
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("parents.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    parent: Mapped["Parent | None"] = relationship(back_populates="resources")

    # Composite indexes
    __table_args__ = (
        Index("ix_resources_name_created", "name", "created_at"),
    )
```

**Conventions:**
- Inherits: `UUIDMixin`, `TimestampMixin`, `Base`
- `Mapped[Type]` with `mapped_column()`
- Indexes on frequently queried columns
- Foreign keys: `ForeignKey("table.id", ondelete="CASCADE")`
- Relationships: `relationship(back_populates="...")`
- Composite indexes: `__table_args__`

### Error Handling

```python
from app.core.exceptions import NotFoundError, ForbiddenError, UnauthorizedError

# In endpoint
case = await svc.get_case(case_id)
if not case:
    raise NotFoundError("Case not found")

# In service with role check
if user.role not in ["administrator", "analyst"]:
    raise ForbiddenError("Analyst role required")

# Pipeline-specific errors
if timeout_exceeded:
    raise PipelineError("Pipeline timeout after 30s")
```

**Conventions:**
- Custom exceptions: `NotFoundError` (404), `ForbiddenError` (403), `UnauthorizedError` (401)
- `HTTPException` with status codes for generic errors
- `PipelineError` for business logic errors (pipeline stages)

### Logging (structlog)

```python
import structlog

logger = structlog.get_logger()

# Event-based logging (key-value pairs)
logger.info("pipeline_started", email_id=str(email_id), case_id=str(case.id))
logger.error("llm_timeout", error=str(exc), case_id=str(case_id), duration_ms=2800)
logger.debug("ml_prediction", score=0.82, confidence=0.95, model="distilbert-v1.2")
```

**Conventions:**
- Key-value pairs in logs (not plain strings)
- Convert UUIDs to strings: `str(uuid)`
- Event names: `pipeline_started`, `pipeline_completed`, `ml_prediction`, `llm_timeout`
- Log levels: `debug` (verbose), `info` (events), `warning` (issues), `error` (failures)

### Authentication (Clerk JWT)

```python
from app.api.deps import CurrentUser, RequireAnalyst, RequireAdmin

# Endpoint with auth (any authenticated user)
@router.get("/profile")
async def get_profile(user: CurrentUser):
    return {"user_id": user.id, "role": user.role}

# Endpoint with role check (analyst or admin)
@router.post("/cases/{case_id}/resolve")
async def resolve_case(case_id: UUID, user: RequireAnalyst):
    # user has role "analyst" or "administrator"
    return {"message": "Case resolved"}

# Endpoint restricted to admins
@router.post("/users")
async def create_user(user: RequireAdmin):
    # user has role "administrator"
    return {"message": "User created"}
```

**Conventions:**
- Dependencies: `CurrentUser` (any auth user), `RequireAnalyst`, `RequireAdmin`
- JWT RS256 with Clerk public PEM key (verify in `app.core.security`)
- Hybrid sync: Clerk auth + local user records in DB
- Token in headers: `Authorization: Bearer <clerk-jwt>`

### Rate Limiting (slowapi)

```python
from fastapi import Request
from app.core.rate_limit import limiter

@router.get("/cases")
@limiter.limit("60/minute")
async def list_cases(request: Request, db: DbSession):
    # Rate limit: 60 requests per minute per IP
    ...

@router.post("/cases/{id}/resolve")
@limiter.limit("10/minute")
async def resolve_case(request: Request, case_id: UUID, db: DbSession):
    # Stricter limit for mutating endpoints
    ...
```

**Conventions:**
- Rate limit decorator above endpoint
- `Request` parameter required (slowapi uses it to get client IP)
- Limits: 100/min (general), 60/min (reads), 10/min (writes)
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

---

## Frontend Patterns

### Vue 3 SFC (Script Setup)

```vue
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { Case } from '@/types/case'
import { fetchCases } from '@/services/caseService'
import { useCasesStore } from '@/stores/cases'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'

// Props
const props = defineProps<{
  caseId: string
  expanded?: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update', value: Case): void
}>()

// Refs
const loading = ref(true)
const data = ref<Case | null>(null)
const error = ref<string | null>(null)

// Computed
const riskLevel = computed(() => data.value?.risk_level ?? 'unknown')
const isHighRisk = computed(() => ['high', 'critical'].includes(riskLevel.value))

// Methods
async function loadData() {
  loading.value = true
  error.value = null
  try {
    data.value = await fetchCases(props.caseId)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}

function handleClose() {
  emit('close')
}

// Watchers
watch(() => props.caseId, () => {
  loadData()
})

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="component">
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" :onRetry="loadData" />
    <div v-else class="content">
      <h2>{{ data?.email.subject }}</h2>
      <span :class="['badge', riskLevel]">{{ riskLevel }}</span>
    </div>
  </div>
</template>

<style scoped>
.component {
  padding: 1rem;
  background-color: var(--bg-card);
  border-radius: 8px;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.badge.high,
.badge.critical {
  background-color: var(--color-error);
  color: white;
}
</style>
```

**Conventions:**
- `<script setup lang="ts">` always
- Props: `defineProps<{...}>()`
- Emits: `defineEmits<{...}>()`
- Refs for local state: `ref<Type>(initialValue)`
- Computed for derived values: `computed(() => ...)`
- Methods: regular async functions
- Watchers: `watch(() => prop, callback)`
- Lifecycle: `onMounted()`, `onUnmounted()`, `watch()`
- Type narrowing: `e instanceof Error`

### Pinia Stores (Composition API)

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Case } from '@/types/case'
import { fetchCases, resolveCase } from '@/services/caseService'

export const useCasesStore = defineStore('cases', () => {
  // State
  const cases = ref<Case[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters (computed)
  const quarantined = computed(() =>
    cases.value.filter(c => c.status === 'quarantined')
  )

  const highRisk = computed(() =>
    cases.value.filter(c => ['high', 'critical'].includes(c.risk_level))
  )

  const totalCount = computed(() => cases.value.length)

  // Actions
  async function fetch(params?: { status?: string; page?: number }) {
    loading.value = true
    error.value = null
    try {
      const result = await fetchCases(params)
      cases.value = result.items
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch cases'
    } finally {
      loading.value = false
    }
  }

  async function resolve(id: string, verdict: string) {
    try {
      const updated = await resolveCase(id, verdict)
      // Update local state
      const index = cases.value.findIndex(c => c.id === id)
      if (index !== -1) {
        cases.value[index] = updated
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to resolve case'
      throw e
    }
  }

  function clear() {
    cases.value = []
    error.value = null
  }

  return {
    // State
    cases,
    loading,
    error,
    // Getters
    quarantined,
    highRisk,
    totalCount,
    // Actions
    fetch,
    resolve,
    clear,
  }
})
```

**Conventions:**
- Composition API (not Options API)
- Return explicit: state, getters (computed), actions
- Async actions with try/catch/finally
- Type narrowing: `e instanceof Error`
- Update local state after mutations
- Clear/reset function for cleanup

### API Services (Axios)

```typescript
import api from './api'
import type { Case, CaseDetail, CaseStatus } from '@/types/case'

export interface ListCasesParams {
  page?: number
  size?: number
  status?: CaseStatus
  risk_level?: string
  date_from?: string
  date_to?: string
}

export interface ListCasesResponse {
  items: Case[]
  total: number
  page: number
  size: number
}

export async function fetchCases(params?: ListCasesParams): Promise<ListCasesResponse> {
  const { data } = await api.get<ListCasesResponse>('/cases', { params })
  return data
}

export async function fetchCaseDetail(id: string): Promise<CaseDetail> {
  const { data } = await api.get<CaseDetail>(`/cases/${id}`)
  return data
}

export async function resolveCase(id: string, verdict: string): Promise<Case> {
  const { data } = await api.post<Case>(`/cases/${id}/resolve`, { verdict })
  return data
}
```

**Conventions:**
- Type generics: `api.get<ResponseType>()`
- Destructuring: `const { data } = await api.get()`
- Export async functions (not default export)
- One file per domain: `caseService.ts`, `emailService.ts`, `dashboardService.ts`
- Interface for request params and response types

### TypeScript Types

```typescript
// Types (union types)
export type CaseStatus = 'pending' | 'analyzing' | 'quarantined' | 'resolved'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type Verdict = 'allowed' | 'warned' | 'quarantined' | 'blocked'

// Interfaces (object structures)
export interface Case {
  id: string
  status: CaseStatus
  risk_level: RiskLevel
  final_score: number | null
  final_verdict: Verdict | null
  created_at: string
  updated_at: string
}

export interface CaseDetail extends Case {
  email: Email | null
  analyses: Analysis[]
  alert_events: AlertEvent[]
}

export interface Email {
  id: string
  sender: string
  recipient: string
  subject: string
  body: string
  received_at: string
}

// Generic API response
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}
```

**Conventions:**
- `type` for union types: `type Status = 'a' | 'b' | 'c'`
- `interface` for object structures
- `| null` for nullable fields (not `Optional<T>`)
- `Record<string, unknown>` for dynamic objects
- Extend interfaces: `interface Detail extends Base { ... }`

### Component Conventions

```vue
<!-- ErrorState.vue -->
<script setup lang="ts">
defineProps<{
  message: string
  onRetry?: () => void
}>()
</script>

<template>
  <div class="error-state">
    <span class="material-symbols-rounded">error</span>
    <p class="message">{{ message }}</p>
    <button v-if="onRetry" @click="onRetry" class="retry-button">
      Retry
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 1rem;
  color: var(--color-error);
}

.message {
  margin: 1rem 0;
  font-size: 0.875rem;
}

.retry-button {
  padding: 0.5rem 1rem;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: var(--color-primary-dark);
}
</style>
```

**Conventions:**
- Props typed with `defineProps<{...}>()`
- Scoped styles: `<style scoped>`
- Material Symbols: `<span class="material-symbols-rounded">icon_name</span>`
- CSS variables: `var(--bg-card)`, `var(--color-primary)`, `var(--border-color)`
- BEM naming for complex components (optional)

---

## Testing Conventions

### Backend (pytest)

```python
import pytest
from uuid import uuid4
from app.services.case_service import CaseService
from app.models.case import Case

@pytest.mark.asyncio
async def test_list_cases(db_session):
    """Test list_cases with pagination."""
    svc = CaseService(db_session)
    result = await svc.list_cases(page=1, size=20)

    assert result["total"] >= 0
    assert len(result["items"]) <= 20
    assert result["page"] == 1
    assert result["size"] == 20

@pytest.mark.asyncio
async def test_get_case_not_found(db_session):
    """Test get_case raises NotFoundError."""
    svc = CaseService(db_session)

    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await svc.get_case(uuid4())
```

**Conventions:**
- `@pytest.mark.asyncio` for async tests
- Fixtures: `db_session`, `test_client`, `auth_headers`
- Coverage: ≥60% (pytest-cov)
- File naming: `tests/unit/test_{module}.py`
- Descriptive docstrings

### Frontend (Vitest)

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import FormInput from '@/components/common/FormInput.vue'

describe('FormInput', () => {
  it('should render label', () => {
    const wrapper = mount(FormInput, {
      props: { modelValue: '', label: 'Email Address' }
    })
    expect(wrapper.text()).toContain('Email Address')
  })

  it('should emit update:modelValue on input', async () => {
    const wrapper = mount(FormInput, {
      props: { modelValue: '', label: 'Test' }
    })

    const input = wrapper.find('input')
    await input.setValue('new value')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['new value'])
  })
})
```

**Conventions:**
- Vue Test Utils for components
- Pinia: `setActivePinia(createPinia())` in `beforeEach`
- Coverage: ≥30% (vitest --coverage)
- Mock external dependencies: `vi.mock('@/services/api')`

---

## Naming Conventions

### Files
- **Components:** PascalCase (`CaseDetailView.vue`, `StatsCard.vue`)
- **Stores:** camelCase (`cases.ts`, `dashboard.ts`)
- **Services:** camelCase (`caseService.ts`, `emailService.ts`)
- **Types:** camelCase (`case.ts`, `email.ts`, `api.ts`)
- **Python modules:** snake_case (`case_service.py`, `email_parser.py`)

### Variables
- **JavaScript/TypeScript:** camelCase (`caseId`, `userName`)
- **Python:** snake_case (`case_id`, `user_name`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_RETRIES`, `API_BASE_URL`)
- **Database:** snake_case (tables: `cases`, columns: `final_score`)

### Git
- **Branches:** `feat/feature-name`, `fix/bug-name`, `docs/doc-name`, `refactor/what`
- **Commits:** Brief, one line, Spanish or English
- **No AI/Claude references in commits**
- **Examples:**
  - ✅ "add rate limiting to quarantine endpoints"
  - ✅ "fix pipeline timeout on ML stage"
  - ❌ "Claude suggested improvements"
  - ❌ "fixed stuff"

---

## Commands

```bash
make dev              # Start all services (db, mlflow, backend, frontend)
make test             # Run all tests
make lint             # ruff + mypy + eslint
make migrate          # Run Alembic migrations
make migration msg="" # Create new migration
make train-ml         # Train ML model
make simulate-email   # Send test email to pipeline
```

**URLs:**
- Backend: `localhost:8000/api/v1`
- Frontend: `localhost:3000`
- Database: `localhost:5432`
- MLflow: `localhost:5000`
- API Docs: `localhost:8000/docs`

---

## Design Decisions

- **Single-tenant** (Strike Security only)
- **Clerk auth** (RS256 JWT, invitation-only, hybrid sync with local users)
- **Pre-delivery interception**, not post-delivery scanning
- **PostgreSQL JSONB** for email metadata (flexible schema)
- **Thesis project:** decisions balance production viability with academic rigor
- **Fail-open pipeline:** if crashes, email is forwarded (avoid blocking legitimate mail)
- **3-layer detection:** Heuristics (fast) + ML (accurate) + LLM (explainable)
- **LLM as third opinion with floor/cap:** Final score is weighted average (H+ML+LLM) with LLM floor (high LLM >= 0.80 enforces minimum) and LLM cap (low LLM < 0.15 reduces false positives)

---

## Resources

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Arquitectura completa, diagramas, ERD
- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - Referencia completa de API REST
- [DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) - Setup local y workflow de desarrollo
- [TESTING.md](docs/TESTING.md) - Estrategia de testing, ejemplos, coverage
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guia de deployment (Vercel, Cloud Run, Neon)
- [SMTP_GATEWAY_DEPLOYMENT.md](docs/SMTP_GATEWAY_DEPLOYMENT.md) - Deploy SMTP gateway en GCP
- [ML_TRAINING_GUIDE.md](docs/ML_TRAINING_GUIDE.md) - Entrenar modelo DistilBERT
