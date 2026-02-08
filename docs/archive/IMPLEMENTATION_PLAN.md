# Guard-IA: Análisis Completo y Próximos Pasos

**Versión:** 0.6
**Fecha:** Febrero 2026
**Proyecto:** Tesis universitaria (ORT Uruguay) para Strike Security
**Estado:** ✅ Auth Fixed (staging funcionando), 🟡 Optimizaciones pendientes

---

## 🎯 Contexto: ¿Dónde Estamos?

### Último Logro ✅
**Auth fix deployado exitosamente (commit `bc261dc`):**
- Problema: PEM public key con `\n` literales → PyJWT no podía parsear
- Solución: Field validator en `config.py` que convierte `\n` literales a saltos de línea reales
- Resultado: Dashboard carga sin 401, staging 100% funcional

### Alcance de la Tesis (MVP Completo)
**Guard-IA es un sistema de detección de fraude por email pre-entrega para Google Workspace.**

**Funcionalidades Core (100% implementadas):**
- ✅ SMTP Gateway (aiosmtpd) - intercepta emails antes de inbox
- ✅ Pipeline de detección 3 capas: Heuristics (5ms) → ML (18ms) → LLM (2-3s)
- ✅ Verdicts automáticos: ALLOW, WARN, QUARANTINE, BLOCK (thresholds configurables)
- ✅ Dashboard de analistas: casos, quarantine, emails, monitoreo
- ✅ Case management: resolución, notas, historial
- ✅ Autenticación Clerk (JWT RS256, RBAC: admin/analyst/auditor)
- ✅ Alertas Slack para casos high/critical
- ✅ Database PostgreSQL 16 (async SQLAlchemy, JSONB metadata)
- ✅ CI/CD (GitHub Actions → Cloud Run + Vercel)
- ✅ Documentación completa (9 archivos .md, 7,000+ líneas)

**Out of Scope (v0.7+):**
- Webhooks para eventos
- Audit trail detallado
- Scaling horizontal (materializado views, Redis cache)
- Settings page UI
- Multi-tenant

---

## 📊 Estado Actual: Scorecard

| Dimensión | Score | Estado | Notas |
|-----------|-------|--------|-------|
| **Features (alcance tesis)** | 95% | ✅ Excelente | Solo falta Settings UI (deferred) |
| **Backend Quality** | 8/10 | ✅ Bueno | 3 import violations, 1 TODO |
| **Frontend Quality** | 9/10 | ✅ Excelente | Arquitectura sólida |
| **Backend Testing** | 55% | ✅ Bueno | Pipeline 92%, DB layer débil |
| **Frontend Testing** | 5% | 🔴 Crítico | Solo services testeados |
| **Security** | 7.5/10 | 🟡 Fair | Rate limiting 15%, HSTS falta |
| **Performance** | 7/10 | 🟡 Fair | ML lazy loading, dashboard 10k+ casos |
| **Documentation** | 9/10 | ✅ Excelente | Falta runbook de incidents |
| **Production Readiness** | 🟡 Fair | Listo con ajustes | Ver sección P0/P1 |

**Overall: 8.2/10** - Proyecto sólido, listo para producción con ajustes menores.

---

## 🔍 Análisis Detallado

### 1. Code Quality (8/10)

#### ✅ Fortalezas
- Indentación consistente (4 spaces Python, 2 spaces TS)
- Type annotations 95%+ (Python 3.11, TypeScript strict)
- Docstrings en todas las funciones públicas
- Async/await correctamente implementado
- LF line endings, UTF-8, no trailing whitespace

#### ⚠️ Issues Encontrados

**Issue #1: Import statements dentro de funciones (CLAUDE.md violation)**
- **Ubicación:** `backend/app/gateway/handler.py:152,154,187`
- **Detalle:** 3 imports dentro de funciones (no en top-level)
  ```python
  # Línea 152
  from app.services.pipeline.orchestrator import analyze_email
  # Línea 154
  from email.utils import parsedate_to_datetime
  # Línea 187
  import re
  ```
- **Impacto:** Viola estándar documentado en CLAUDE.md
- **Fix:** Mover imports al top del archivo
- **Tiempo:** 5 minutos

**Issue #2: TODO sin resolver**
- **Ubicación:** `backend/app/services/pipeline/orchestrator.py:252`
- **Detalle:** `# TODO: Alert service removed - re-implement if needed`
- **Fix:** Remover comentario o crear issue en backlog
- **Tiempo:** 2 minutos

**Issue #3: Código comentado (legacy)**
- **Ubicación:** `backend/app/services/pipeline/heuristics.py:178-185`
- **Detalle:** Bloque de scoring antiguo comentado (git history preserva)
- **Fix:** Eliminar bloque comentado
- **Tiempo:** 2 minutos

---

### 2. Testing Coverage

#### Backend: 55% (✅ Bueno)

**Coverage por módulo:**
```
Pipeline (orchestrator)    92%  ✅ Excelente
Heuristics engine          93%  ✅ Excelente
ML classifier              92%  ✅ Excelente
LLM explainer              92%  ✅ Excelente
Models (SQLAlchemy)        94%  ✅ Excelente
API endpoints              75%  ✅ Bueno
Auth layer                 67%  🟡 Fair
Database utilities         47%  🔴 Débil
```

**Issue: Integration tests usan AsyncMock en vez de DB real**
- **Impacto:** Queries SQL no validadas, relaciones no testeadas, race conditions no detectadas
- **Fix:** Migrar a PostgreSQL test database (testcontainers)
- **Tiempo:** 4 horas
- **Prioridad:** P1 (alta)

#### Frontend: 5% (🔴 Crítico)

**Tests escritos:**
- ✅ `dashboard.spec.ts` - 84 líneas, 5 test cases
- ✅ `caseService.spec.ts` - 135 líneas, 7 test cases
- ⚠️ `cases.spec.ts` - 85 líneas (estructura, sin tests)

**Missing (0% coverage):**
- ❌ Component tests: ErrorState, FormInput, LoadingState
- ❌ Store tests: cases, emails, dashboard, monitoring
- ❌ Composable tests: useAuth, useApi, useFilters
- ❌ View tests: CaseDetailView, EmailExplorerView, MonitoringView
- ❌ E2E tests: 9 archivos creados pero vacíos

**Setup:**
- ✅ Vitest configurado
- ✅ Playwright configurado
- ✅ CI/CD ejecuta `npm run test` (pero pasa porque casi no hay tests)

**Impacto:** Frontend logic sin validación, alto riesgo de regresiones.

**Fix:**
- **Mínimo (30% coverage):** 12 horas
  - Store tests (cases, dashboard)
  - Component tests (ErrorState, FormInput)
  - 5 E2E flows críticos
- **Ideal (60% coverage):** 24 horas
  - Full store + component + composable tests
  - 10+ E2E flows

**Prioridad:** P0 (crítico para producción)

---

### 3. Security Assessment

#### ✅ Fortalezas (7.5/10)

**Authentication (10/10):**
- JWT RS256 verification con Clerk public key
- Audience claim validation (`settings.clerk_publishable_key`)
- Token expiration/nbf checks
- Public key caching (5-minute TTL)
- Error handling correcto

**Authorization (9/10):**
- RBAC: administrator, analyst, auditor
- Dependencies tipadas: `CurrentUser`, `RequireAnalyst`, `RequireAdmin`
- No privilege escalation encontrado

**HTTPS/TLS (8/10):**
- Nginx redirect HTTP → HTTPS ✅
- TLS 1.2/1.3 enforced ✅
- Security headers (X-Frame-Options, CSP, X-Content-Type-Options) ✅
- ⚠️ HSTS header falta (Strict-Transport-Security)

**CORS (7/10):**
- No wildcard origins ✅
- Lista explícita de dominios ✅
- HTTPS validation en producción ✅
- ⚠️ Dominios de producción no configurados (solo localhost)

**Input Validation (8/10):**
- Pydantic v2 schemas en todos los endpoints ✅
- Field constraints (min_length, max_length, ge, le) ✅
- Email format validation ✅
- Type checking completo ✅

#### 🟡 Issues de Seguridad (No blockers)

**Issue #1: .env files NO están en repo (✅ VERIFICADO)**
- **Status:** .env.local, .env.staging, .env.production están en `.gitignore`
- **Git history:** Sin commits con .env files
- **Conclusión:** ✅ Secrets NO expuestos (STATUS_REVIEW estaba desactualizado)

**Issue #2: Rate limiting incompleto (15% endpoints)**
- **Protected (4 endpoints):**
  - POST `/ingest` - 100/min ✅
  - GET `/emails` - 300/min ✅
  - GET `/emails/{id}` - 500/min ✅
  - GET `/cases` - 60/min ✅

- **Unprotected (17 endpoints):**
  - POST `/cases/{id}/resolve` ❌
  - POST `/quarantine/{id}/release` ❌
  - POST `/quarantine/{id}/delete` ❌
  - GET `/monitoring/stats` ❌
  - GET `/dashboard` ❌
  - Y otros 12 endpoints

- **Riesgo:** DOS attacks, API abuse
- **Fix:** Agregar `@limiter.limit("X/minute")` a todos los endpoints
- **Tiempo:** 2 horas
- **Prioridad:** P1 (alta)

**Issue #3: HSTS header missing**
- **Ubicación:** `infra/docker/nginx.conf`
- **Missing:** `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **Riesgo:** SSL stripping attacks en primera visita
- **Fix:** Agregar header a nginx.conf
- **Tiempo:** 15 minutos
- **Prioridad:** P1 (alta)

**Issue #4: CORS production domains missing**
- **Current:** Solo `localhost:3000`, `localhost:5173`
- **Missing:** `https://guardia.strikesecurity.com`, `https://guardia-staging.vercel.app`
- **Ubicación:** `backend/app/core/security.py` o variables de entorno
- **Riesgo:** Frontend production bloqueado o requiere wildcard (inseguro)
- **Fix:** Agregar dominios a CORS_ORIGINS
- **Tiempo:** 10 minutos
- **Prioridad:** P1 (alta)

---

### 4. Performance

#### ✅ Optimizaciones Completadas
- N+1 query fixed (500ms → 50ms para 100 casos)
- URL resolver connection leak fixed
- Race conditions en orchestrator eliminadas
- Query optimization con `selectinload()`

#### 🟡 Issues de Performance

**Issue #1: ML Model Lazy Loading (+2000ms en primera request)**
- **Síntoma:** Primera predicción: 2020ms; siguientes: 18ms
- **Causa:** Modelo carga en primera predicción, no en startup
- **Fix:** Preload en FastAPI lifespan event
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Preload ML model
      if settings.pipeline_ml_enabled:
          from app.services.pipeline.ml_classifier import MLClassifier
          classifier = MLClassifier()
          await classifier.preload()
      yield
  ```
- **Tiempo:** 30 minutos
- **Prioridad:** P2 (media)

**Issue #2: Dashboard query con 10k+ casos (2-3s load time)**
- **Síntoma:** Con datasets grandes (>10k casos), queries lentas
- **Causa:** Large IN clauses en PostgreSQL
- **Workaround actual:** Pagination (100 casos/página) ✅
- **Long-term fix:** Materialized view (v0.7+)
- **Impacto:** Bajo (solo deployments con 10k+ casos)
- **Prioridad:** P3 (baja, deferred a v0.7)

**Issue #3: Frontend bundle size**
- **Current:** 434 KB uncompressed, ~120 KB gzipped
- **Status:** ✅ ACEPTABLE (< 500 KB threshold)
- **Breakdown:**
  - Chart.js: ~85 KB (necesario)
  - Vue + Router + Pinia: ~60 KB (necesario)
  - Clerk SDK: ~35 KB (necesario)
  - Otros: ~9 KB
- **Prioridad:** N/A (no optimizar por ahora)

---

### 5. Frontend UX

#### ✅ Componentes Comunes Creados (v0.6)
- `ErrorState.vue` (47 líneas) - usado en 5 views
- `FormInput.vue` (71 líneas) - usado en 4 views
- `LoadingState.vue` (49 líneas) - usado en 4 views
- **Impacto:** ~150-200 líneas de código duplicado eliminadas

#### 🟡 UX Issue

**Issue #1: MonitoringView modal no usa FormInput component**
- **Ubicación:** `frontend/src/views/MonitoringView.vue:420-520`
- **Detalle:** ~100 líneas de HTML/CSS duplicadas para modal filter
- **Fix:** Refactorizar a `FormInput` component
- **Tiempo:** 1 hora
- **Prioridad:** P2 (media, mejora UX)

**Issue #2: FormTextarea component falta**
- **Uso:** Case notes, email bodies
- **Workaround actual:** HTML `<textarea>` raw
- **Fix:** Crear `FormTextarea.vue` (similar a FormInput)
- **Tiempo:** 45 minutos
- **Prioridad:** P2 (media)

---

### 6. Documentation

#### ✅ Excelente (9/10)

**Archivos existentes (7,000+ líneas):**
- `ARCHITECTURE.md` (882 líneas) - Diagramas, ERD, data flow
- `API_DOCUMENTATION.md` (865 líneas) - Todos los endpoints con ejemplos
- `TESTING.md` (1,038 líneas) - Estrategias, ejemplos, coverage
- `ONBOARDING.md` (759 líneas) - Setup para developers
- `ML_TRAINING_GUIDE.md` (742 líneas) - Entrenar modelo DistilBERT
- `RUN_LOCAL.md` (367 líneas) - Desarrollo local
- `CLAUDE.md` (in repo) - Standards completos
- `README.md` + `README.es.md` - Descripción general

**Plus:**
- OpenAPI/Swagger auto-generado (`/docs`)
- Docstrings en todas las funciones públicas
- Inline comments para lógica compleja

#### 🟡 Docs Faltantes

**Missing #1: Deployment Runbook**
- **Contenido:** Incident response, rollbacks, log analysis, GCP debugging
- **Uso:** On-call engineers, production incidents
- **Tiempo:** 3 horas
- **Prioridad:** P1 (alta para producción)

**Missing #2: Troubleshooting Guide**
- **Nota:** Mencionado en CLAUDE.md pero no existe
- **Contenido:** Problemas comunes, errores típicos, soluciones
- **Tiempo:** 2 horas
- **Prioridad:** P2 (media)

---

## 🚀 Próximos Pasos: Roadmap Priorizado

### 🔴 Priority 0: Blockers de Producción (CRÍTICO)

#### P0-1: Frontend Test Suite (12 horas)
**Objetivo:** Llegar a 30%+ coverage (mínimo viable para producción)

**Tasks:**
1. **Store tests (4h):**
   - `cases.spec.ts` - CRUD, filters, pagination
   - `dashboard.spec.ts` - metrics loading, error handling
   - `emails.spec.ts` - list, detail, search

2. **Component tests (3h):**
   - `ErrorState.spec.ts` - render, retry callback
   - `FormInput.spec.ts` - v-model, validation, error states
   - `LoadingState.spec.ts` - render, spinner

3. **E2E tests (5h):**
   - Login flow
   - Case detail view → resolve
   - Quarantine release/delete
   - Dashboard metrics load
   - Email explorer search

**Resultado esperado:**
- Coverage: 5% → 30%+
- CI/CD: Tests pasan (actualmente pasan vacíos)
- Confianza: Alta para deploys

**Prioridad:** 🔴 CRÍTICO (sin esto, producción es riesgosa)

---

### 🟡 Priority 1: Alta (Pre-Producción) - 6 horas

#### P1-1: Rate Limiting Completo (2h)
**Objetivo:** Proteger todos los endpoints críticos

**Endpoints a proteger:**
```python
# API v1 (17 endpoints)
POST /cases/{id}/resolve          - 10/min
POST /cases/{id}/notes            - 20/min
POST /quarantine/{id}/release     - 10/min
POST /quarantine/{id}/delete      - 10/min
POST /quarantine/{id}/keep        - 10/min
GET  /dashboard                   - 60/min
GET  /monitoring/stats            - 60/min
GET  /monitoring/pipeline         - 60/min
GET  /monitoring/costs            - 60/min
GET  /cases/{id}                  - 100/min
GET  /auth/me                     - 100/min
POST /auth/sync                   - 5/min
# ... (otros 5 endpoints)
```

**Template:**
```python
from app.core.rate_limit import limiter

@router.post("/cases/{id}/resolve")
@limiter.limit("10/minute")
async def resolve_case(request: Request, ...):
    ...
```

**Verificación:**
- Todos los endpoints tienen `@limiter.limit()`
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- Test: `curl -I` en staging para verificar headers

---

#### P1-2: Security Headers (30min)
**Objetivo:** HSTS + CORS production

**1. HSTS Header (15min):**
```nginx
# infra/docker/nginx.conf
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**2. CORS Production (15min):**
```python
# backend/app/config.py o .env.staging/.env.production
CORS_ORIGINS=https://guardia-staging.vercel.app,https://guardia.strikesecurity.com
```

**Verificación:**
```bash
# HSTS
curl -I https://guardia-api-staging-zwa7epaviq-ue.a.run.app | grep Strict-Transport

# CORS
curl -H "Origin: https://guardia-staging.vercel.app" \
  https://guardia-api-staging-zwa7epaviq-ue.a.run.app/api/v1/health | grep Access-Control
```

---

#### P1-3: Backend Integration Tests con DB Real (4h)
**Objetivo:** Validar SQL queries, relaciones, transacciones

**Approach:**
- Usar `testcontainers-python` para PostgreSQL ephemeral
- Migrar tests de `AsyncMock` a real DB
- Focus: case_service, email_service, quarantine_service

**Template:**
```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg

@pytest.fixture
async def db_session(postgres):
    engine = create_async_engine(postgres.get_connection_url())
    # Run migrations
    await run_alembic_migrations(engine)
    # Create session
    async with AsyncSession(engine) as session:
        yield session
```

**Resultado:**
- Coverage DB layer: 47% → 70%+
- SQL queries validadas
- Relaciones (selectinload) testeadas

---

#### P1-4: Deployment Runbook (3h)
**Objetivo:** Guía para incident response, rollbacks, debugging

**Contenido:**
1. **Incident Response:**
   - High error rate (>5%)
   - Pipeline timeouts (>30s)
   - Database connection errors
   - Rate limit DoS

2. **Rollback Procedures:**
   - Cloud Run revision rollback
   - Vercel deployment rollback
   - Database migration rollback (Alembic downgrade)

3. **Log Analysis:**
   - GCP Cloud Logging queries
   - structlog event filtering
   - Error aggregation

4. **Common Issues:**
   - 401 Unauthorized (JWT expired, PEM key issue)
   - 500 Internal Error (DB connection, pipeline crash)
   - ML model timeout (>5s)
   - LLM rate limit (OpenAI)

**Ubicación:** `docs/RUNBOOK.md`

---

### 🟢 Priority 2: Media (Post-Producción) - 7 horas

#### P2-1: Code Quality Cleanup (30min)
**Tasks:**
1. Mover imports de `handler.py` al top (5min)
2. Remover TODO de `orchestrator.py` (2min)
3. Eliminar código comentado de `heuristics.py` (2min)
4. Extraer magic numbers a `constants.py` (20min)

**Verificación:**
```bash
# Check imports
ruff check backend/app/gateway/handler.py

# Check TODOs
grep -r "TODO" backend/app/services/

# Check commented code
grep -r "^#.*=" backend/app/services/
```

---

#### P2-2: ML Model Preloading (30min)
**Objetivo:** Eliminar +2000ms en primera request

**Fix:**
```python
# backend/app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Preload ML model
    if settings.pipeline_ml_enabled:
        logger.info("preloading_ml_model")
        from app.services.pipeline.ml_classifier import MLClassifier
        classifier = MLClassifier()
        await classifier.preload()  # Load model + tokenizer
        logger.info("ml_model_loaded", duration_ms=elapsed)

    yield

    # Shutdown: Cleanup
    logger.info("shutdown")

app = FastAPI(lifespan=lifespan)
```

**Resultado:**
- Primera request: 2020ms → 18ms
- Mejora: +2000ms

---

#### P2-3: Frontend UX Improvements (2h)
**Tasks:**
1. **FormTextarea component (45min):**
   - Similar a FormInput
   - Usar en case notes, email bodies
   - Props: modelValue, label, rows, error

2. **MonitoringView modal refactor (1h):**
   - Reemplazar HTML raw por FormInput
   - Eliminar ~100 líneas CSS duplicadas
   - Consistencia UX

3. **Loading states en vistas (15min):**
   - Verificar que todas las vistas usan LoadingState
   - Eliminar spinners custom

---

#### P2-4: Troubleshooting Guide (2h)
**Objetivo:** Documentar problemas comunes y soluciones

**Contenido:**
1. **Auth Issues:**
   - 401 Unauthorized
   - JWT expired
   - PEM key parse error
   - Clerk session invalid

2. **Pipeline Issues:**
   - Timeout (>30s)
   - ML model not loading
   - LLM rate limit
   - Heuristics crash

3. **Database Issues:**
   - Connection pool exhausted
   - Migration conflicts
   - Slow queries

4. **Frontend Issues:**
   - API 500 errors
   - CORS blocked
   - Blank dashboard

**Ubicación:** `docs/TROUBLESHOOTING.md`

---

#### P2-5: E2E Test Suite Expansion (2h)
**Objetivo:** Cubrir flows adicionales (coverage 30% → 50%)

**Flows adicionales:**
1. Email detail → create case
2. Case filtering (status, risk, date)
3. Dashboard metrics drill-down
4. User profile view
5. Quarantine bulk actions

**Tech:** Playwright, Page Object Model

---

### 🔵 Priority 3: Baja (v0.7+) - No urgente

#### P3-1: Dashboard Query Optimization
- Materialized view para stats
- Redis cache para metrics
- **Deferred:** Solo si >10k casos

#### P3-2: Settings Page UI
- View `/settings` (route existe, componente falta)
- User preferences, pipeline config
- **Deferred:** Low priority (v0.7)

#### P3-3: Webhook Notifications
- POST endpoint para eventos críticos
- Slack fallback
- **Deferred:** Out of scope tesis

#### P3-4: Advanced Audit Logging
- Detailed audit trail (who, what, when)
- Compliance (SOC 2, GDPR)
- **Deferred:** v0.7+

---

## 📅 Timeline Recomendado

### Semana 1: Blockers + Alta Prioridad (18h)
```
Día 1 (6h):
  - P0-1: Frontend test suite básico (stores + components)

Día 2 (6h):
  - P0-1: E2E tests (5 flows críticos)
  - P1-1: Rate limiting (17 endpoints)

Día 3 (6h):
  - P1-2: Security headers (HSTS, CORS)
  - P1-3: Integration tests con DB real
  - P1-4: Deployment runbook

📊 Al final de Semana 1:
  ✅ Frontend coverage: 30%+
  ✅ Rate limiting: 100% endpoints
  ✅ Security: HSTS + CORS production
  ✅ Runbook completo
  → READY FOR PRODUCTION
```

### Semana 2: Optimizaciones (7h)
```
Día 4 (3h):
  - P2-1: Code quality cleanup
  - P2-2: ML model preloading

Día 5 (4h):
  - P2-3: Frontend UX improvements
  - P2-4: Troubleshooting guide

📊 Al final de Semana 2:
  ✅ Code quality: 9/10
  ✅ Performance: +2000ms mejora primera request
  ✅ UX: FormTextarea, MonitoringView refactor
  ✅ Docs: Troubleshooting completo
  → PRODUCTION POLISHED
```

### Semana 3+: Expansión (opcional, v0.7)
```
- P2-5: E2E test suite expansion (50% coverage)
- P3-1: Dashboard query optimization (si >10k casos)
- P3-2: Settings page UI
- Backlog: Webhooks, audit logging, scaling
```

---

## 🎯 Conclusión

### Estado Actual: ✅ Excelente Base
**Guard-IA v0.6 es un proyecto de tesis universitaria técnicamente sólido:**

**✅ Fortalezas:**
- Arquitectura de 3 capas (heuristics + ML + LLM) funcionando
- Backend FastAPI async con PostgreSQL 16
- Frontend Vue 3 Composition API con Pinia
- Auth Clerk (JWT RS256) implementado correctamente
- CI/CD con GitHub Actions → Cloud Run + Vercel
- Documentación completa (7,000+ líneas)
- Pipeline metrics & monitoring
- Alcance de tesis 100% completo

**🟡 Áreas de Mejora (no blockers):**
- Frontend testing 5% (crítico subir a 30%+)
- Rate limiting 15% (subir a 100%)
- Performance: ML lazy loading (+2000ms primera request)
- UX: FormTextarea, MonitoringView refactor

**🔴 Blockers Resueltos:**
- ✅ Auth 401 fixed (PEM parsing)
- ✅ Secrets NO están en repo (.gitignore correcto)

### Recomendación Final

**Para PRODUCCIÓN (requisito mínimo):**
1. ✅ **Semana 1 completa** (P0 + P1) - 18 horas
   - Frontend tests 30%+
   - Rate limiting 100%
   - Security headers
   - Runbook

**Para EXCELENCIA (proyecto polished):**
2. ✅ **Semana 2 completa** (P2) - 7 horas adicionales
   - Code quality cleanup
   - Performance optimizations
   - UX improvements
   - Troubleshooting docs

**Total investment: 25 horas (~3-4 días de trabajo) para estar production-ready + polished.**

---

## 📝 Documento Generado

**Este documento reemplaza a:**
- `STAGING_AUTH_FIX_CHECKLIST.md` (borrar)
- Plan anterior (obsoleto)

**Next steps:**
1. Revisar este documento
2. Priorizar tasks (¿empezar por P0-1 frontend tests?)
3. Ejecutar semana 1 (P0 + P1)
4. Deploy a producción 🚀

**¿Preguntas? ¿Ajustar prioridades?**
