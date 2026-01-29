# Guard-IA v0.2 — Project Status Review & Next Steps

> Exhaustive review completed January 2026. Every backend and frontend file was audited.

---

## 1. PROJECT HEALTH SCORECARD

| Area | Status | Score |
|------|--------|-------|
| **Pipeline (Heuristic + ML + LLM)** | Functional, well-architected | 9/10 |
| **Backend API** | Functional, missing auth on most endpoints | 6/10 |
| **Frontend Views** | Functional, several non-functional UI elements | 6/10 |
| **Database & Models** | Solid, minor bugs | 8/10 |
| **Authentication** | Working but incomplete enforcement | 5/10 |
| **Testing** | Mostly stubs — minimal real coverage | 2/10 |
| **Documentation** | Excellent (ARCHITECTURE.md, README) | 9/10 |
| **Deployment** | Staging fully operational (Cloud Run + Vercel) | 8/10 |
| **Code Quality** | Clean, no console.logs, no TODOs in app code | 8/10 |

**Overall: ~6.5/10** — Core pipeline works well, but security enforcement, test coverage, and UI polish need work for v0.2.

---

## 2. STRENGTHS (What works well)

### Pipeline & Detection
- 3-layer pipeline is fully operational: Heuristic (~5ms) + ML (~18ms) + LLM (~2-3s)
- Weighted scoring with graceful degradation (auto-adjusts if layers unavailable)
- Heuristic engine is comprehensive: auth/domain/URL/keyword sub-engines with correlation bonuses
- LLM Explainer has Claude primary + GPT fallback
- Fail-open design in SMTP gateway — if pipeline crashes, email forwards
- 20-email test suite validated scoring coherence (7 allowed, 5 warned, 6 quarantined, 2 blocked)

### Backend Architecture
- Clean service-layer pattern: API → Service → DB
- Async throughout (SQLAlchemy async, asyncpg, httpx)
- Pydantic v2 validation
- structlog JSON logging (no print/console debug)
- Multi-env config with Pydantic Settings
- Comprehensive models (16 tables with proper FKs, cascading, constraints)
- 16 Pydantic v2 schema files for request/response validation

### Frontend
- Zero `console.log` or `TODO` in app code
- Zero `any` types — fully typed TypeScript
- Strict tsconfig
- Clean dark-theme UI with consistent design language
- Dashboard with 10 widget components and Chart.js
- CaseDetailView is excellent: 3-tab layout, score ring animation, sandboxed iframe for HTML email, note CRUD
- 27 reusable components organized in 6 categories

### DevOps
- Staging fully deployed: Cloud Run (backend) + Vercel (frontend) + Neon (DB)
- Multi-env configuration (.env.local, .env.staging)
- Docker support
- Comprehensive architecture documentation (ARCHITECTURE.md + bilingual README)

---

## 3. BUGS (Must fix)

### Critical - DONE

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| B1 | **Admin role check broken** — `deps.py` checks for `"admin"` but `UserRole` enum is `"administrator"` | `backend/app/api/deps.py:76` vs `core/constants.py:135-138` | Admin users can never pass RequireAdmin |
| B2 | **PDF export returns plain text as application/pdf** — not a valid PDF file | `backend/app/services/report_service.py:78-93` | Report downloads are corrupted |
| B3 | **`total_cases` hardcoded to 0** in dashboard API response | `backend/app/services/dashboard_service.py:146` | Dashboard shows wrong KPI |
| B4 | **Pipeline health `stages` accessed wrong** — view reads `pipeline_health.stages.heuristic.avg_ms` but type has `stage_avg_ms: Record<string, number>` | `frontend/src/views/DashboardView.vue:71-73` vs `types/dashboard.ts:22-27` | Stage badges show fallback values always |
| B5 | **`fp_reviews` not in CaseDetail type** — CaseDetailView accesses `caseData.fp_reviews?.length` which is always undefined | `frontend/src/types/case.ts:121-125` + `CaseDetailView.vue:592` | FP review count never shown |
| B6 | **`p95_duration_ms` hardcoded to 0.0** in pipeline health response | `backend/app/services/dashboard_service.py:243` | Pipeline health shows wrong metric |

### High - DONE

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| B7 | **Alerts never triggered** — `evaluate_and_fire()` exists but is never called from the pipeline orchestrator | `backend/app/services/alert_service.py` + `pipeline/orchestrator.py:49-185` | Alert rules are defined but never fire |
| B8 | **Date filters not wired** — CasesView and EmailExplorerView have date filter UI but never send params to API | `frontend/src/views/CasesView.vue:112-119,351` + `EmailExplorerView.vue:27-32,86-88` | Date filtering does nothing |
| B9 | **Threat category descriptions in Spanish** mixed with English UI | `frontend/src/views/CaseDetailView.vue:110-141` | i18n inconsistency |
| B10 | **No 404 route** — unknown paths show blank page | `frontend/src/router/index.ts` | Poor UX |

---

## 4. SECURITY GAPS - TO DO

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| S1 | **No auth on most GET endpoints** — cases (lines 36-84), emails (24-56), dashboard (12-48), alerts (22-105), policies (25-124), reports (15-35), settings (14-29) are all public | `backend/app/api/v1/*.py` | CRITICAL |
| S2 | **Email ingest endpoint has no auth** — anyone can POST emails | `backend/app/api/v1/emails.py:15-21` | HIGH |
| S3 | **JWT audience verification disabled** — `verify_aud: False` means tokens from any Clerk app are accepted | `backend/app/core/security.py:19` | MEDIUM |
| S4 | **RequireAdmin/RequireAnalyst/RequireAuditor never used** — RBAC deps exist but no endpoint uses them | `backend/app/api/deps.py:76-78` | HIGH |
| S5 | **No role-based route guards** on frontend — `requireRole()` guard exists but is never applied to any route | `frontend/src/router/guards.ts:5-12` | MEDIUM |
| S6 | **No role validation on write endpoints** — alerts CRUD, policies CRUD accept any authenticated user (no admin/analyst check) | `backend/app/api/v1/alerts.py:35,62,83` + `policies.py:38-154` | MEDIUM |

---

## 5. NON-FUNCTIONAL UI ELEMENTS - DONE

Buttons/features that are rendered but do nothing:

| # | Element | Location |
|---|---------|----------|
| U1 | **Export CSV** button (CasesView) — no `@click` handler | `CasesView.vue:181-184` |
| U2 | **Ingest Email** button (EmailExplorerView) — no `@click` handler | `EmailExplorerView.vue:55-58` |
| U3 | **Export** button (EmailExplorerView) — no `@click` handler | `EmailExplorerView.vue:59-62` |
| U4 | **Release Selected** button (QuarantineView) — no handler | `QuarantineView.vue:59-62` |
| U5 | **Batch Actions** button (QuarantineView) — no handler | `QuarantineView.vue:63-66` |
| U6 | **"View Full" link** (QuarantineView) — `href="#"` with no click handler | `QuarantineView.vue:118` |
| U7 | **Global search** in topbar — styled div with placeholder text, not an input | `AppTopbar.vue:47-50` |
| U8 | **Settings link** in topbar points to `/settings` route that doesn't exist | `AppTopbar.vue:57-68` |
| U9 | **Email row click** — no `@click` handler on `<tr>`, rows are not clickable | `EmailExplorerView.vue:108` |
| U10 | **Checkbox column** in EmailExplorerView — no `v-model` binding, no selection logic | `EmailExplorerView.vue:108-134` |

---

## 6. UNUSED CODE / DEAD CODE - DONE

### Components created but never imported (14 total):
- `components/shared/RiskBadge.vue`
- `components/shared/EmptyState.vue`
- `components/shared/ConfirmDialog.vue`
- `components/shared/ScoreGauge.vue`
- `components/shared/StatusTag.vue`
- `components/cases/CaseTable.vue`
- `components/cases/CaseFilters.vue`
- `components/pipeline/PipelineStage.vue`
- `components/pipeline/LLMExplanation.vue`
- `components/quarantine/QuarantineTable.vue`
- `components/quarantine/QuarantineActions.vue`
- `components/quarantine/EmailPreview.vue`
- `components/layout/AppBreadcrumb.vue`
- `components/dashboard/TopSenders.vue` (fully implemented but not rendered in DashboardView)

### Services with no consumers:
- `settingsService.ts` — full CRUD but no settings view/store
- `filterOptions.ts` — `dateRangeToParams` and `DATE_RANGE_OPTIONS` exported but never used

### Sidebar missing link:
- Notifications view/route exist but sidebar has no "Notifications" menu item (only accessible via topbar icon)

### Router guard unused:
- `requireRole()` in `router/guards.ts` is defined but never applied to any route

---

## 7. PERFORMANCE CONCERNS

| # | Issue | Location |
|---|-------|----------|
| P1 | **Sync ML inference in async context** — `torch.no_grad()` + model forward pass blocks event loop (~18ms) | `backend/app/services/pipeline/ml_classifier.py:131-132` |
| P2 | **Sync file I/O in async methods** — `path.write_bytes()`, `path.read_bytes()`, `path.unlink()` block event loop | `backend/app/gateway/storage.py:35,45,52` |
| P3 | **Sync Clerk SDK in async function** — `clerk.users.get()` is blocking HTTP call | `backend/app/services/user_sync_service.py:18-19` |
| P4 | **Pipeline timeout config unused** — `pipeline_timeout_seconds=30` defined but never enforced with `asyncio.wait_for()` | `backend/app/config.py` + `pipeline/orchestrator.py` |
| P5 | **No frontend build optimization** — no chunk splitting or compression plugin in Vite config | `frontend/vite.config.ts` |

---

## 8. TESTING STATUS

### Current state: Minimal effective coverage

**Configuration:**
- `tests/conftest.py` — EXISTS (async test setup with fixtures)

**Unit tests** (`tests/unit/`) — 8 files:
- `test_heuristics.py` — has real test logic
- `test_orchestrator.py` — has real test logic
- `test_parser.py` — has real test logic
- `test_security.py` — has real test logic
- `test_alert_service.py` — has test logic
- `test_llm_explainer.py` — has test logic
- `test_ml_classifier.py` — has test logic

**API tests** (`tests/api/`) — 4 files:
- `test_auth.py` — stubs with `pass` + TODO
- `test_emails.py` — stubs with `pass` + TODO
- `test_cases.py` — stubs with `pass` + TODO
- `test_dashboard.py` — stubs with `pass` + TODO

**Integration tests** (`tests/integration/`) — 3 files:
- `test_email_ingestion.py` — stub
- `test_pipeline_flow.py` — stub
- `test_quarantine_flow.py` — stubs

**Summary:** Unit tests have some real logic, but all API and integration tests are stubs. No end-to-end coverage of the HTTP layer.

---

## 9. STYLE & CONSISTENCY ISSUES

| # | Issue |
|---|-------|
| C1 | NotificationsView uses PrimeVue (Button, Tag, ProgressSpinner) while rest of app uses custom dark-theme CSS |
| C2 | Email scores show `toFixed(2)` in EmailExplorerView but percentage in CasesView — inconsistent format |
| C3 | No i18n framework — all UI text hardcoded, Spanish mixed in CaseDetailView threat descriptions (lines 110-141) |
| C4 | Lazy imports inside methods (`import torch`, `import anthropic`, `import openai`) violate project's "imports at top" rule |
| C5 | `datetime.utcnow()` deprecated usage in report_service.py (should use `datetime.now(timezone.utc)`) |

---

## 10. RECOMMENDED NEXT STEPS (v0.2 Backlog)

### Priority 1 — Must Have (Bugs + Security)

1. **Fix admin role check** — change `deps.py:76` from `"admin"` to `"administrator"` or update the enum
2. **Add auth to all API GET endpoints** — apply `CurrentUser` dependency to cases, emails, dashboard, alerts, policies, reports, settings
3. **Apply RBAC** — use `RequireAdmin`, `RequireAnalyst`, `RequireAuditor` where appropriate on write endpoints
4. **Fix dashboard `total_cases`** — compute actual count instead of hardcoded 0
5. **Fix pipeline health `stages` type mismatch** — align DashboardView property access with `stage_avg_ms: Record<string, number>`
6. **Fix `fp_reviews` type** — add to CaseDetail interface in `types/case.ts`
7. **Wire alert evaluation** — call `evaluate_and_fire()` from pipeline orchestrator after analysis
8. **Wire date filters** — CasesView and EmailExplorerView need to pass date params to store/API
9. **Add 404 route** — catch-all redirect or NotFoundView
10. **Fix PDF export** — use a real PDF library (reportlab, weasyprint) or switch to CSV-only

### Priority 2 — Should Have (UX Polish)

11. **Add loading/error states to DashboardView** — show spinner while fetching, error banner on failure
12. **Remove or implement non-functional buttons** — Export CSV, Ingest Email, Release Selected, Batch Actions, global search
13. **Add Notifications to sidebar** — route and view exist but no menu link
14. **Add `/settings` route and view** — or remove the link from topbar
15. **Migrate NotificationsView from PrimeVue to custom CSS** — match rest of app
16. **Render TopSenders in Dashboard** — component is ready, just not imported
17. **Unify score display format** — pick percentage or decimal, use everywhere
18. **Fix Spanish threat category descriptions** — translate to English or add i18n

### Priority 3 — Nice to Have (Quality & Performance)

19. **Write real API tests** — replace stubs in test_auth, test_cases, test_emails, test_dashboard
20. **Write integration tests** — pipeline flow end-to-end, quarantine flow
21. **Wrap ML inference in `asyncio.to_thread()`** — prevent event loop blocking
22. **Wrap file I/O in `asyncio.to_thread()`** — storage.py operations
23. **Use async Clerk SDK** or `asyncio.to_thread()` for user sync
24. **Enforce pipeline timeout** — wrap orchestrator.analyze() in `asyncio.wait_for()`
25. **Enable JWT audience verification** — set `verify_aud: True` with correct audience
26. **Clean up unused components** — delete or integrate the 14 unused components
27. **Add Vite chunk splitting** — optimize frontend build
28. **Add ConfirmDialog** before quick allow/block in CasesView

### Priority 4 — Future (v0.3+)

29. **Add email detail view** — click email row in EmailExplorerView to see detail
30. **Implement global search** — functional search across cases/emails
31. **Add notification navigation** — click notification to go to referenced case
32. **Add i18n framework** (vue-i18n) for proper Spanish/English support
33. **Add accessibility** — ARIA labels, focus management, keyboard navigation
34. **Implement real-time updates** — WebSocket or SSE for new case notifications
35. **Add CI/CD pipeline** — GitHub Actions for lint + test + deploy
36. **Make JIT provisioning role configurable** — instead of hardcoded "analyst" default

---

## 11. FILES TO MODIFY (by priority group)

### Priority 1
- `backend/app/api/deps.py` — fix role string ("admin" → "administrator")
- `backend/app/api/v1/cases.py` — add `CurrentUser` to GET endpoints (lines 36, 65, 76)
- `backend/app/api/v1/emails.py` — add `CurrentUser` to GET endpoints (lines 24, 49)
- `backend/app/api/v1/dashboard.py` — add `CurrentUser` (line 12)
- `backend/app/api/v1/alerts.py` — add `CurrentUser` to GET endpoints (lines 22, 52, 96) + RBAC on write (35, 62, 83)
- `backend/app/api/v1/policies.py` — add `CurrentUser` to GET endpoints (lines 25, 55, 91, 117) + RBAC on write
- `backend/app/api/v1/reports.py` — add `CurrentUser` (line 15)
- `backend/app/api/v1/settings.py` — add `CurrentUser` to GET (lines 14, 22)
- `backend/app/api/v1/notifications.py` — add `CurrentUser` to PUT (line 31)
- `backend/app/services/dashboard_service.py` — fix total_cases (line 146) + p95 (line 243)
- `backend/app/services/pipeline/orchestrator.py` — wire alert evaluation after analysis
- `backend/app/services/report_service.py` — fix PDF generation (lines 78-93)
- `frontend/src/views/DashboardView.vue` — fix stages access (lines 71-73)
- `frontend/src/views/CaseDetailView.vue` — fix Spanish strings (lines 110-141)
- `frontend/src/views/CasesView.vue` — wire date filter in applyFilters() (lines 112-119)
- `frontend/src/views/EmailExplorerView.vue` — wire date filter in applyFilters() (lines 27-32)
- `frontend/src/types/case.ts` — add fp_reviews to CaseDetail (lines 121-125)
- `frontend/src/router/index.ts` — add 404 catch-all route

### Priority 2
- `frontend/src/components/layout/AppSidebar.vue` — add Notifications link (lines 23-28)
- `frontend/src/views/NotificationsView.vue` — migrate from PrimeVue to custom CSS
- `frontend/src/views/DashboardView.vue` — render TopSenders component
- `frontend/src/components/layout/AppTopbar.vue` — fix settings link (lines 57-68)

### Priority 3
- `backend/tests/api/test_auth.py` — replace stubs with real tests
- `backend/tests/api/test_cases.py` — replace stubs with real tests
- `backend/tests/api/test_emails.py` — replace stubs with real tests
- `backend/tests/api/test_dashboard.py` — replace stubs with real tests
- `backend/tests/integration/test_pipeline_flow.py` — replace stubs
- `backend/tests/integration/test_quarantine_flow.py` — replace stubs
- `backend/app/services/pipeline/ml_classifier.py` — asyncio.to_thread (line 131)
- `backend/app/gateway/storage.py` — asyncio.to_thread (lines 35, 45, 52)
- `backend/app/services/user_sync_service.py` — async Clerk or to_thread (line 18)
- `backend/app/core/security.py` — enable aud verification (line 19)
