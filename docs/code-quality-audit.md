# Guard-IA — Code Quality Audit

**Scope**: Dashboard, Cases, Quarantine, Emails (frontend views + backend services)
**Date**: January 2026

---

## 1. Executive Summary

The 4 main views are functional and visually aligned with the Pencil prototypes. The codebase follows a consistent architecture (Vue 3 Composition API + Pinia stores + FastAPI services). However, there are **significant DRY violations** across the frontend views — roughly 300+ lines of duplicated utility functions and 500+ lines of duplicated CSS. The backend services are well-structured but also contain repeated list-building patterns.

**Overall Grade**: B — Solid foundation, needs a refactoring pass to extract shared utilities before adding more views.

---

## 2. Frontend — View-Level Analysis

### 2.1 DashboardView.vue (124 lines) — GOOD

**Strengths:**
- Clean delegation to 6 sub-components (StatsCard, ThreatChart, RiskDistribution, RecentCases, PipelineHealth, ActiveAlerts)
- Minimal script logic — just a store fetch on mount
- CSS grid layout is responsive and well-structured
- Data flows cleanly: store → props → child components

**Issues:**
- None significant. This is the best-structured view.

---

### 2.2 CasesView.vue (654 lines) — NEEDS REFACTORING

**Strengths:**
- Custom HTML table matches prototype pixel-perfect
- Computed pagination with smart ellipsis logic
- Filter bar with search + dropdowns + clear button
- Proper loading/empty states

**Issues:**

| Issue | Severity | Lines |
|-------|----------|-------|
| `shortId()`, `formatDate()`, `scoreColor()`, `riskColor()`, `riskBg()`, `actionColor()`, `actionBg()`, `statusColor()`, `statusBg()`, `capitalize()` — all duplicated in EmailExplorerView and QuarantineView | High | 77-165 |
| `pageNumbers` computed with ellipsis logic — duplicated exactly in EmailExplorerView | High | 28-45 |
| `.btn-outline`, `.filter-bar`, `.search-input`, `.table-card`, `.pill-badge`, `.pagination`, `.page-btn` CSS — duplicated across 3 views | High | 363-639 |
| `onSearchInput()` and `onFilterChange()` are trivial wrappers that add no value | Low | 65-71 |
| Filter options (`riskOptions`, `actionOptions`, etc.) are hardcoded strings, not sourced from a shared constant | Medium | 15-18 |

---

### 2.3 QuarantineView.vue (699 lines) — NEEDS REFACTORING

**Strengths:**
- Split-panel layout is well-implemented
- Auto-select first item via `watch()` is good UX
- Email preview with metadata, auth badges, AI analysis box
- Responsive breakpoint collapses to stacked layout

**Issues:**

| Issue | Severity | Lines |
|-------|----------|-------|
| `shortId()`, `formatDate()`, `riskColor()`, `riskBg()`, `capitalize()` — all duplicated from CasesView | High | 10-51 |
| `.btn-outline`, `.btn-icon`, `.header-left h1` CSS — duplicated from CasesView | High | 245-331 |
| `formatTimeAgo()` is unique to this view but should be a shared utility | Low | 21-29 |
| `.pill-badge` equivalent styles exist but under different class names (`.item-risk-badge`) | Medium | 427-437 |
| Action buttons (release/keep/delete) don't show loading state during API calls | Medium | 207-228 |
| No error handling shown to user when release/keep/delete fails | Medium | — |

---

### 2.4 EmailExplorerView.vue (605 lines) — NEEDS REFACTORING

**Strengths:**
- Local state management (not using a Pinia store) — appropriate for a simpler view
- Checkbox UI for bulk selection is started
- Table structure matches Cases pattern for consistency

**Issues:**

| Issue | Severity | Lines |
|-------|----------|-------|
| `formatDate()`, `scoreColor()`, `riskColor()`, `riskBg()`, `actionColor()`, `actionBg()`, `capitalize()` — all duplicated from CasesView | High | 79-131 |
| `pageNumbers` computed — exact copy from CasesView | High | 25-42 |
| Entire pagination CSS block (~80 lines) — exact copy from CasesView | High | 535-594 |
| Entire table CSS block (~60 lines) — near-exact copy from CasesView | High | 413-533 |
| `filterShow` dropdown has "Show All" in both the placeholder AND the options list | Low | 168-170 |
| Does NOT use a Pinia store — inconsistent with Cases and Quarantine which do | Medium | — |
| Checkbox state is not tracked — `<input type="checkbox">` has no v-model | Medium | 199 |
| "Ingest Email" button has no click handler | Low | 145-148 |
| "Export" button has no click handler | Low | 149-152 |

---

## 3. Duplicated Code Inventory

### 3.1 Utility Functions (copied across 3 views)

```
Function          | CasesView | QuarantineView | EmailExplorerView
------------------|-----------|----------------|------------------
shortId()         |    YES    |      YES       |        NO
formatDate()      |    YES    |      YES       |       YES
scoreColor()      |    YES    |       NO       |       YES
riskColor()       |    YES    |      YES       |       YES
riskBg()          |    YES    |      YES       |       YES
actionColor()     |    YES    |       NO       |       YES
actionBg()        |    YES    |       NO       |       YES
statusColor()     |    YES    |       NO       |        NO
statusBg()        |    YES    |       NO       |        NO
capitalize()      |    YES    |      YES       |       YES
pageNumbers       |    YES    |       NO       |       YES
```

**Impact**: ~150 lines of JavaScript duplicated. Any color/logic change must be updated in 2-3 places.

### 3.2 Duplicated CSS (~500+ lines)

```
CSS Pattern             | CasesView | QuarantineView | EmailExplorerView
------------------------|-----------|----------------|------------------
.btn-outline            |    YES    |      YES       |       YES
.btn-icon               |    YES    |      YES       |       YES
.header-left h1         |    YES    |      YES       |       YES
.count-badge            |    YES    |       NO       |       YES
.filter-bar             |    YES    |       NO       |       YES
.search-input-wrapper   |    YES    |       NO       |       YES
.search-input           |    YES    |       NO       |       YES
.filter-select          |    YES    |       NO       |       YES
.table-card             |    YES    |       NO       |       YES
.pill-badge             |    YES    |       NO       |       YES
.pagination             |    YES    |       NO       |       YES
.page-btn               |    YES    |       NO       |       YES
.loading-state          |    YES    |       NO       |       YES
.empty-state            |    YES    |       NO       |       YES
.text-muted             |    YES    |       NO       |       YES
```

**Impact**: Any visual change to shared elements (buttons, badges, tables, pagination) must be updated in multiple files.

---

## 4. Backend — Service-Level Analysis

### 4.1 Pattern Consistency

All 3 list services (`case_service`, `quarantine_service`, `email_service`) follow the same pattern:

```python
# Pattern used in all 3 services:
1. Build SELECT query with filters
2. Count total with subquery
3. Apply offset/limit
4. Execute and iterate to build dicts
5. Return {"items": [...], "total": N, "page": P, "size": S}
```

This is good consistency but also means any improvement to the pattern (caching, cursor pagination, etc.) must be applied 3 times.

### 4.2 Backend Issues

| Issue | File | Severity |
|-------|------|----------|
| `list_cases()` and `list_quarantined()` both build identical item dicts manually with the same 12 keys | `case_service.py:60-82`, `quarantine_service.py:42-62` | High (DRY) |
| `email_service.list_emails()` filters `risk_level` in Python instead of SQL (post-fetch filter) — breaks pagination counts | `email_service.py:102-107` | High (Bug) |
| `import` inside function body (`from app.models.email import Email`) in `case_service.py:45-46` | `case_service.py:45` | Medium |
| `selectinload` imported inside function body in `quarantine_service.py:27` and `email_service.py:55` | multiple | Medium |
| `_persist_email` in `handler.py:133` has `import` inside method body | `handler.py:135-137` | Medium |
| No input sanitization on `search` param — `ilike(f"%{search}%")` passes user input directly | `case_service.py:48`, `email_service.py:62` | Medium |

### 4.3 Critical Bug: Email List Pagination with risk_level

In `email_service.py:96-108`:
```python
# This filters AFTER fetching — pagination count is wrong
if risk_level and item["risk_level"] != risk_level:
    continue
items.append(item)

if risk_level:
    total = len(items)  # This gives items on THIS page, not total matching
```

The `risk_level` filter is applied in Python after the SQL query returns results. This means:
- Page 1 might show 18 items instead of 25 (because 7 were filtered out)
- `total` reflects only the current page's filtered count, not the real total
- Pagination is broken when this filter is active

**Fix**: Join `Case` in the SQL query and filter by `Case.risk_level` in the WHERE clause.

---

## 5. Stores Analysis

### 5.1 Consistency

| Feature | cases.ts | quarantine.ts | EmailExplorer |
|---------|----------|---------------|---------------|
| Uses Pinia store | YES | YES | NO (local refs) |
| Has loading state | YES | YES | YES (local ref) |
| Has error state | YES | YES | NO (silent catch) |
| Has setPage() | YES | YES | YES (local fn) |
| Has setFilters() | YES | NO | NO |
| Auto-fetches on mount | In view | In view | In view |

The EmailExplorerView manages its own state locally instead of through a Pinia store. This is inconsistent with Cases/Quarantine and means the email data is lost on navigation and not available to other components (e.g., sidebar badge counts).

### 5.2 Store Issues

- **cases.ts**: `setPage()` and `setFilters()` call `fetchCases()` immediately — no debounce on search input means rapid API calls.
- **quarantine.ts**: `release()`, `keep()`, `remove()` don't have error handling — if the API call fails, `selectedId` and `emailDetail` are still cleared.
- **EmailExplorer**: `loadEmails()` has a bare `catch {}` that silently swallows errors.

---

## 6. Refactoring Recommendations (Priority Order)

### P0 — Fix Bugs

1. **Fix email list risk_level filter** — Move to SQL JOIN with `Case.risk_level` in WHERE clause
2. **Fix quarantine actions error handling** — Don't clear selection on API failure

### P1 — Extract Shared Utilities

3. **Create `src/utils/formatters.ts`** — Move `formatDate()`, `formatTimeAgo()`, `shortId()`, `capitalize()` here
4. **Create `src/utils/colors.ts`** — Move `scoreColor()`, `riskColor()`, `riskBg()`, `actionColor()`, `actionBg()`, `statusColor()`, `statusBg()` here
5. **Create `src/utils/pagination.ts`** — Export `computePageNumbers(currentPage, totalPages)` as a composable or pure function
6. **Create `src/constants/filterOptions.ts`** — Move `riskOptions`, `actionOptions`, `statusOptions`, `dateOptions` to shared constants

### P2 — Extract Shared CSS

7. **Create `src/assets/components.css`** (or move to existing `variables.css`):
   - `.btn-outline`, `.btn-primary`, `.btn-success`, `.btn-icon`
   - `.page-header`, `.header-left`, `.header-right`
   - `.count-badge`, `.pill-badge`, `.text-muted`
   - `.filter-bar`, `.search-input-wrapper`, `.search-input`, `.filter-select`, `.clear-link`
   - `.table-card`, `.loading-state`, `.empty-state`
   - `.pagination`, `.pagination-info`, `.pagination-buttons`, `.page-btn`, `.page-ellipsis`

   This would eliminate ~500 lines of duplicated scoped CSS.

### P3 — Improve Consistency

8. **Create email Pinia store** — Move EmailExplorer local state to `src/stores/emails.ts` for consistency and data persistence across navigation
9. **Add search debounce** — Use `useDebounceFn` from VueUse (or a simple setTimeout) on search inputs to avoid rapid API calls
10. **Add loading state to quarantine actions** — Show spinner/disabled state during release/keep/delete operations

### P4 — Backend Improvements

11. **Extract shared list builder** — Create a base `paginated_list()` helper in a base service or utility module to reduce repeated query patterns
12. **Move imports to file top** — Move the `from app.models.email import Email` and `selectinload` imports to the top of files per project convention
13. **Sanitize search input** — Escape `%` and `_` characters in search parameters to prevent LIKE injection

---

## 7. Scalability Assessment

**What's easy to add right now:**
- New views with tables (copy pattern from CasesView)
- New dashboard cards (StatsCard component is reusable)
- New filter options (add to dropdown arrays)
- New badge types (add color mapping entries)

**What would be painful right now:**
- Changing button styles globally (update 3+ files)
- Changing table styling globally (update 3+ files)
- Changing color palette (update 10+ hardcoded color maps across 3 views)
- Adding dark/light theme support (colors hardcoded in JS, not CSS variables)
- Adding real-time updates (no WebSocket infrastructure, views poll on mount only)

**After refactoring (P1-P3):**
- All of the above "painful" items become single-file changes
- New views would import shared utilities instead of copying 150+ lines
- Color palette changes would touch 1 file (`colors.ts`) instead of 3

---

## 8. Positive Patterns to Preserve

1. **Composition API + `<script setup>`** — Clean, modern Vue 3 pattern
2. **Pinia stores with async actions** — Proper separation of data fetching from views
3. **Scoped CSS** — No style leaks between components
4. **Responsive breakpoints** — All views have `@media (max-width: 1200px)` rules
5. **CSS variables** — Core theme colors are defined in `variables.css`
6. **Backend service pattern** — Consistent `__init__(db)` + method pattern across all services
7. **Type safety** — TypeScript interfaces for all API responses
8. **Loading/empty states** — Every data-fetching view shows appropriate states

---

## Summary

The codebase is functional and consistent in architecture. The main area for improvement is extracting ~700 lines of duplicated code (150 JS + 500 CSS) into shared utilities and global styles. The `email_service.py` risk_level filter bug should be fixed immediately as it breaks pagination. After the P1-P2 refactoring, adding new views would require ~50% less boilerplate code.
