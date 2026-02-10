# Guard-IA - Analisis de Limpieza v0.2

Auditoria completa del 100% de los archivos del proyecto para identificar codigo muerto, features placeholder, y oportunidades de simplificacion.

---

## Resumen Ejecutivo

El proyecto tiene **~1,000 lineas de codigo muerto** distribuidas en modelos, servicios y configuraciones que fueron creados para features futuras que nunca se implementaron. El core del pipeline (heuristics, ML, LLM, cases, emails, quarantine, dashboard, monitoring) esta limpio y bien conectado end-to-end.

---

## 1. Tablas de Base de Datos

### Tablas ACTIVAS (10)

| Tabla | Uso | Critica |
|-------|-----|---------|
| `emails` | Core: ingesta SMTP, pipeline, API queries | SI |
| `cases` | Core: pipeline, resolucion, quarantine, dashboard | SI |
| `analyses` | Core: resultados H/ML/LLM por caso | SI |
| `evidences` | Core: senales detectadas por heuristicas y ML | SI |
| `users` | Auth: sync con Clerk JWT | SI |
| `policy_entries` | Pipeline: bypass checker + blacklist/whitelist | SI |
| `quarantine_actions` | Audit trail de release/keep/delete | NO |
| `case_notes` | Notas del analista en casos | NO |
| `fp_reviews` | Reviews de falsos positivos | NO |
| `alembic_version` | Control de migraciones | SI |

### Tablas SIN USO - ELIMINAR (5)

| Tabla | Motivo de eliminacion |
|-------|----------------------|
| `alert_rules` | No hay CRUD, no hay endpoints, no hay servicio. Solo el modelo ORM existe. |
| `alert_events` | Solo se lee en dashboard (`_get_active_alerts`), pero NUNCA se crean registros. El query siempre retorna lista vacia. Feature no implementada. |
| `notifications` | Modelo existe pero NO esta exportado en `__init__.py`. No hay servicio, no hay endpoints, 0 referencias en el codigo. |
| `custom_rules` | Modelo exportado pero nunca referenciado en ningun servicio, endpoint, ni pipeline. |
| `settings` | Toda la configuracion es via `.env` / Pydantic Settings. La tabla nunca se consulta ni se actualiza. |

---

## 2. Backend - Archivos Sin Uso

### Servicios

| Archivo | Lineas | Estado | Motivo |
|---------|--------|--------|--------|
| `app/services/slack_service.py` | 173 | ELIMINAR | `SlackDeliveryService` esta implementado pero **nunca se importa** desde ningun otro archivo. Es codigo huerfano. |

### Modelos

| Archivo | Lineas | Estado | Motivo |
|---------|--------|--------|--------|
| `app/models/alert_event.py` | ~25 | ELIMINAR | Tabla sin uso real |
| `app/models/alert_rule.py` | ~25 | ELIMINAR | Tabla sin uso real |
| `app/models/notification.py` | ~31 | ELIMINAR | Ni siquiera esta exportado en `__init__.py` |
| `app/models/custom_rule.py` | ~24 | ELIMINAR | Nunca referenciado |
| `app/models/setting.py` | ~17 | ELIMINAR | Nunca consultado |

### Config (`app/config.py`) - Variables sin uso

| Variable | Motivo |
|----------|--------|
| `slack_webhook_url` | Solo referenciada por `slack_service.py` que es codigo muerto |
| `frontend_base_url` | Solo referenciada por `slack_service.py` |
| `mlflow_tracking_uri` | MLflow se usa en `/ml/` para training, no en el backend en runtime |
| `rate_limit_storage_uri` | Definida pero nunca usada por slowapi (usa default `memory://`) |

### Constants (`app/core/constants.py`) - Enums sin uso

| Enum | Motivo |
|------|--------|
| `AlertChannel` (EMAIL, SLACK) | Solo usado en slack_service.py (muerto) |
| `AlertDeliveryStatus` (PENDING, DELIVERED, FAILED) | Solo usado en slack_service.py (muerto) |

### .env - Variables a eliminar

| Variable | Archivos | Motivo |
|----------|----------|--------|
| `SLACK_WEBHOOK_URL` | `.env.example`, `.env.staging`, `backend/.env.example` | Feature no implementada |
| `FRONTEND_BASE_URL` | `.env.example`, `.env.staging`, `backend/.env.example` | Solo usada por Slack (muerto) |
| `MLFLOW_TRACKING_URI` | `.env.example`, `backend/.env.example` | No usado en backend runtime |

---

## 3. Frontend - Archivos Sin Uso

### Componentes

| Archivo | Estado | Motivo |
|---------|--------|--------|
| `components/monitoring/HeuristicsTopRules.vue` | ELIMINAR | Componente huerfano, nunca importado ni renderizado en ninguna vista |

### Dashboard - ActiveAlerts

| Archivo | Estado | Motivo |
|---------|--------|--------|
| `components/dashboard/ActiveAlerts.vue` | ELIMINAR | Muestra `active_alerts` del dashboard, pero la query siempre retorna lista vacia porque nadie crea AlertEvents |

### Tipos

| Tipo | Archivo | Estado | Motivo |
|------|---------|--------|--------|
| `TopRulePoint` | `types/monitoring.ts` | ELIMINAR | Solo usado por `HeuristicsTopRules.vue` (huerfano) |
| `ActiveAlertItem` | `types/dashboard.ts` | ELIMINAR | Solo usado por `ActiveAlerts.vue` (a eliminar) |

---

## 4. Dashboard Service - Codigo Muerto

| Metodo | Archivo | Estado | Motivo |
|--------|---------|--------|--------|
| `_get_active_alerts()` | `app/services/dashboard_service.py` | ELIMINAR | Query a `alert_events` que siempre retorna vacio. Incluye import de `AlertEvent` y `AlertRule`. |

El campo `active_alerts` en el response del dashboard tambien se elimina del schema.

---

## 5. Infraestructura

### Scripts

| Archivo | Estado | Motivo |
|---------|--------|--------|
| `infra/scripts/seed-db.sh` | ELIMINAR | Stub con solo TODOs. Seeding se hace via `backend/scripts/seed_emails.py` |

### Workflows, Docker, Makefile

Todos los workflows (4), docker-compose, Dockerfile, Makefile estan activos y funcionales. No hay limpieza necesaria.

---

## 6. Archivos que se MANTIENEN (confirmado uso activo)

### Backend (todos usados)
- `app/api/v1/` - 7 endpoint files, todos registrados en router
- `app/services/case_service.py`, `email_service.py`, `dashboard_service.py`, `monitoring_service.py`, `quarantine_service.py`, `user_sync_service.py`
- `app/services/pipeline/` - orchestrator, heuristics, ml_classifier, llm_explainer, bypass_checker, url_resolver, models, heuristic_data
- `app/services/ingestion/queue.py`
- `app/gateway/` - server, handler, parser, relay, storage
- `app/core/security.py`, `exceptions.py`, `rate_limit.py`
- `app/models/` - email, case, analysis, evidence, user, policy_entry, quarantine_action, case_note, fp_review

### Frontend (todos usados)
- 6 vistas, todas con rutas activas
- 34 de 35 componentes activos
- 6 stores, todos usados
- 4 services, todos con endpoints backend validos
- 4 utilities, todos referenciados

### Scripts (todos usados)
- `backend/scripts/seed_emails.py`, `simulate_email.py`, `email_templates.py`, `download_model.py`

---

## 7. Plan de Ejecucion Propuesto

### Paso 1: Migration Alembic
- DROP TABLE: `alert_events`, `alert_rules`, `notifications`, `custom_rules`, `settings`

### Paso 2: Eliminar archivos backend
- `app/models/alert_event.py`
- `app/models/alert_rule.py`
- `app/models/notification.py`
- `app/models/custom_rule.py`
- `app/models/setting.py`
- `app/services/slack_service.py`
- Limpiar `app/models/__init__.py` (remover imports/exports de modelos eliminados)

### Paso 3: Limpiar config y constants
- Remover de `app/config.py`: `slack_webhook_url`, `frontend_base_url`, `mlflow_tracking_uri`, `rate_limit_storage_uri`
- Remover de `app/core/constants.py`: `AlertChannel`, `AlertDeliveryStatus`
- Limpiar `.env.example`, `.env.staging`, `backend/.env.example`

### Paso 4: Limpiar dashboard service
- Remover metodo `_get_active_alerts()` de `dashboard_service.py`
- Remover campo `active_alerts` del schema de dashboard
- Remover imports de `AlertEvent`, `AlertRule`

### Paso 5: Limpiar frontend
- Eliminar `components/dashboard/ActiveAlerts.vue`
- Eliminar `components/monitoring/HeuristicsTopRules.vue`
- Remover import/uso de `ActiveAlerts` en `DashboardView.vue`
- Remover tipo `ActiveAlertItem` de `types/dashboard.ts`
- Remover tipo `TopRulePoint` de `types/monitoring.ts`

### Paso 6: Eliminar infra stub
- Eliminar `infra/scripts/seed-db.sh`

### Paso 7: Verificacion
- Correr tests: `cd backend && .venv/bin/python -m pytest tests/ -v`
- Correr lint: `ruff check app/`
- Build frontend: `cd frontend && npx vite build`
- Verificar que dashboard carga sin errores

---

_Generado: Febrero 2026_
