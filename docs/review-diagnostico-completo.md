# Guard-IA: Diagnostico Completo del Repositorio

**Fecha**: Enero 2026
**Estado general**: ~20-25% implementado
**Veredicto**: Infraestructura solida, logica de negocio pendiente

---

## 1. ESTADO ACTUAL DEL REPOSITORIO

### Resumen ejecutivo

El proyecto tiene una arquitectura bien definida y toda la infraestructura/configuracion esta lista. Sin embargo, **toda la logica de negocio** (servicios, endpoints, pipeline) esta sin implementar. Los endpoints devuelven `pass` y los servicios lanzan `NotImplementedError`.

### Mapa de implementacion por modulo

```
BACKEND
├── config.py                    ✅ Completo
├── main.py                      ✅ Completo (FastAPI + CORS + health check)
├── core/
│   ├── security.py              ✅ Completo (JWT create/validate, bcrypt)
│   ├── constants.py             ✅ Completo (enums, roles, weights)
│   └── exceptions.py            ✅ Completo (custom HTTP exceptions)
├── db/
│   └── session.py               ✅ Completo (async SQLAlchemy + asyncpg)
├── models/
│   ├── base.py                  ✅ Completo (UUID + timestamps mixins)
│   ├── user.py                  ✅ Completo
│   ├── email_artifact.py        ✅ Completo (JSONB headers/urls/attachments)
│   ├── case.py                  ✅ Completo
│   ├── decision.py              ✅ Completo
│   ├── evidence.py              ✅ Completo
│   ├── alert.py                 ✅ Completo
│   ├── notification.py          ✅ Completo
│   └── policy.py                ✅ Completo
├── schemas/
│   ├── auth.py                  ✅ Completo (LoginRequest, TokenResponse)
│   ├── case.py                  ✅ Completo
│   ├── email.py                 ✅ Completo
│   ├── decision.py              ✅ Completo
│   ├── evidence.py              ✅ Completo
│   ├── alert.py                 ✅ Completo
│   ├── policy.py                ✅ Completo
│   ├── dashboard.py             ✅ Completo
│   ├── quarantine.py            ✅ Completo
│   ├── notification.py          ✅ Completo
│   ├── report.py                ✅ Completo
│   └── user.py                  ✅ Completo
├── api/
│   ├── deps.py                  ❌ CRITICO: get_current_user_id() no implementado
│   ├── middleware/auth.py       ✅ Completo (HTTPBearer extractor)
│   ├── middleware/logging.py    ✅ Completo (structlog)
│   ├── v1/router.py             ✅ Completo (todos los sub-routers registrados)
│   ├── v1/auth.py               ❌ login/refresh = pass
│   ├── v1/emails.py             ❌ ingest/list/get = pass
│   ├── v1/cases.py              ❌ list/get/resolve = pass
│   ├── v1/dashboard.py          ❌ get_stats = pass
│   ├── v1/quarantine.py         ❌ list/approve/reject = pass
│   ├── v1/policies.py           ❌ CRUD completo = pass
│   ├── v1/alerts.py             ❌ list/mark_read = pass
│   ├── v1/reports.py            ❌ export = pass
│   ├── v1/notifications.py      ❌ list/mark_read = pass
│   └── v1/settings.py           ⚠️  GET hardcodeado, PUT = pass
├── services/
│   ├── auth_service.py          ❌ authenticate/refresh/create_user = NotImplementedError
│   ├── email_service.py         ❌ ingest/list/get = NotImplementedError
│   ├── case_service.py          ❌ list/get/resolve = NotImplementedError
│   ├── dashboard_service.py     ❌ get_stats = NotImplementedError
│   ├── quarantine_service.py    ❌ list/approve/reject = NotImplementedError
│   ├── alert_service.py         ❌ NotImplementedError
│   ├── policy_service.py        ❌ CRUD = NotImplementedError
│   ├── notification_service.py  ❌ NotImplementedError
│   ├── report_service.py        ❌ generate_csv/pdf = NotImplementedError
│   └── pipeline/
│       ├── orchestrator.py      ❌ analyze() = NotImplementedError
│       │                        ✅ _determine_risk_level() implementado
│       │                        ✅ _determine_action() implementado
│       ├── heuristics.py        ❌ 4 sub-engines retornan 0.0
│       ├── ml_classifier.py     ❌ predict() = NotImplementedError
│       └── llm_explainer.py     ❌ explain() = NotImplementedError
└── tests/
    ├── conftest.py              ✅ Completo (AsyncClient fixture)
    ├── unit/test_security.py    ✅ Completo (tests pasan)
    ├── unit/test_heuristics.py  ❌ Skeleton (pass)
    ├── unit/test_ml_classifier.py ❌ Skeleton (pass)
    ├── unit/test_orchestrator.py  ❌ Skeleton (pass)
    ├── unit/test_llm_explainer.py ❌ Skeleton (pass)
    ├── api/test_auth.py         ❌ Skeleton (pass)
    ├── api/test_cases.py        ❌ Skeleton (pass)
    ├── api/test_emails.py       ❌ Skeleton (pass)
    ├── api/test_dashboard.py    ❌ Skeleton (pass)
    └── integration/             ❌ Todos skeleton (pass)

FRONTEND
├── main.ts                      ✅ Completo (Vue + Pinia + PrimeVue)
├── router/index.ts              ✅ Completo (todas las rutas + lazy loading)
├── router/guards.ts             ✅ Completo (requireRole)
├── services/
│   ├── api.ts                   ✅ Completo (axios + interceptors)
│   ├── authService.ts           ✅ Completo
│   ├── caseService.ts           ✅ Completo
│   ├── dashboardService.ts      ✅ Completo
│   ├── emailService.ts          ✅ Completo
│   ├── quarantineService.ts     ✅ Completo
│   └── reportService.ts         ✅ Completo
├── stores/
│   ├── auth.ts                  ✅ Completo (token persistence)
│   ├── cases.ts                 ⚠️  fetchCases() = TODO
│   ├── dashboard.ts             ⚠️  fetchDashboard() = TODO
│   ├── quarantine.ts            ⚠️  fetchQuarantined() = TODO
│   ├── notifications.ts         ⚠️  fetchNotifications() = TODO
│   └── settings.ts              ⚠️  Thresholds hardcodeados
├── composables/
│   ├── useApi.ts                ✅ Completo
│   ├── useAuth.ts               ✅ Completo
│   ├── usePagination.ts         ✅ Completo
│   └── useFilters.ts            ✅ Completo
├── types/                       ✅ Todo completo
├── views/
│   ├── LoginView.vue            ✅ Completo (implementado desde Pencil)
│   └── DashboardView.vue        ✅ Completo (implementado desde Pencil)
└── components/
    ├── layout/AppSidebar.vue    ✅ Completo (implementado desde Pencil)
    ├── layout/AppTopbar.vue     ✅ Completo (implementado desde Pencil)
    ├── layout/AppLayout.vue     ✅ Completo
    ├── dashboard/StatsCard.vue  ✅ Completo
    ├── dashboard/ThreatChart.vue ✅ Completo
    ├── dashboard/RiskDistribution.vue ✅ Completo
    ├── dashboard/RecentCases.vue ✅ Completo
    ├── dashboard/PipelineHealth.vue ✅ Completo
    └── dashboard/ActiveAlerts.vue ✅ Completo

ML MODULE
├── src/config.py                ✅ Completo (hyperparams, MLflow config)
├── src/train.py                 ❌ Skeleton (TODO con guia detallada)
├── src/predict.py               ❌ Skeleton (TODO con guia)
├── src/preprocess.py            ⚠️  preprocess_text() implementado, resto TODO
└── src/evaluate.py              ❌ Skeleton (metricas target definidas)

INFRAESTRUCTURA
├── docker-compose.yml           ✅ Completo (4 servicios)
├── Makefile                     ✅ Completo (todos los targets)
├── .env.example                 ✅ Completo
├── README.md                    ✅ Completo
├── CLAUDE.md                    ✅ Completo
├── backend/Dockerfile           ✅ Completo (multi-stage)
├── infra/docker/nginx.conf      ✅ Completo (SPA routing)
└── infra/scripts/setup-dev.sh   ✅ Completo
```

### Conteo de implementacion

| Categoria | Completo | Skeleton/TODO | Total | % Completo |
|-----------|----------|---------------|-------|------------|
| **Modelos ORM** | 9 | 0 | 9 | 100% |
| **Schemas Pydantic** | 12 | 0 | 12 | 100% |
| **Core (security, constants, exceptions)** | 3 | 0 | 3 | 100% |
| **Infraestructura (Docker, Make, env)** | 6 | 0 | 6 | 100% |
| **Servicios backend** | 0 | 10 | 10 | 0% |
| **Endpoints API** | 1 | 10 | 11 | ~9% |
| **Pipeline (3 stages + orchestrator)** | 0 | 4 | 4 | 0% |
| **Tests** | 2 | 11 | 13 | 15% |
| **ML module** | 1 | 4 | 5 | 20% |
| **Frontend services/types** | 10 | 0 | 10 | 100% |
| **Frontend stores** | 2 | 4 | 6 | 33% |
| **Frontend views/components** | 11 | 0 | 11 | 100% |

---

## 2. POR QUE LOGIN MUESTRA "INVALID CREDENTIALS"

### Cadena de fallo

```
1. Frontend: useAuth.login() llama authService.login(email, password)
2. authService: POST /api/v1/auth/login { email, password }
3. Backend auth.py: @router.post("/login") → body es `pass` (retorna null/422)
4. Incluso si llamara AuthService.authenticate(), este lanza NotImplementedError
5. El dependency get_current_user_id() en deps.py siempre lanza UnauthorizedError
```

**Archivos involucrados:**
- `backend/app/api/v1/auth.py:10-12` — endpoint `POST /login` es `pass`
- `backend/app/services/auth_service.py:10-12` — `authenticate()` lanza `NotImplementedError`
- `backend/app/api/deps.py:14-16` — `get_current_user_id()` lanza `UnauthorizedError("Not implemented")`

**Conclusion:** No es un bug. La autenticacion no esta implementada. El backend es un esqueleto.

---

## 3. COMO PROBAR LA APP LOCAL CON DATOS MOCK

### Opcion A: Solo frontend (sin backend)

La forma mas rapida de ver la UI funcionando:

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar en dev mode
npm run dev
```

El frontend ya tiene datos mock hardcodeados en los componentes del dashboard (StatsCard, ThreatChart, RecentCases, etc.). La unica pantalla bloqueada es el login, porque intenta autenticar contra el backend.

**Para saltear el login temporalmente**, editar `src/stores/auth.ts` y forzar `isAuthenticated`:

```typescript
// TEMPORAL: Agregar al final del store
// Para desarrollo sin backend
export function useMockAuth() {
  const store = useAuthStore()
  store.token = 'mock-dev-token'
  store.user = {
    id: '00000000-0000-0000-0000-000000000001',
    email: 'admin@strikesecurity.com',
    full_name: 'Admin Dev',
    role: 'administrator',
    is_active: true,
  }
}
```

Y en `src/views/LoginView.vue`, agregar un boton "Dev Login" que llame `useMockAuth()` y navegue a `/dashboard`.

### Opcion B: Frontend + Backend con Docker

```bash
# Desde la raiz del proyecto

# 1. Copiar environment
cp .env.example .env

# 2. Levantar servicios de infraestructura
docker compose up -d db mlflow

# 3. Esperar a que PostgreSQL este listo (~5s)
# Verificar: docker compose logs db | tail -5

# 4. Instalar dependencias del backend
cd backend
pip install -e ".[dev]"

# 5. Ejecutar migraciones (si existen)
alembic upgrade head

# 6. Iniciar backend
uvicorn app.main:app --reload --port 8000

# 7. En otra terminal, iniciar frontend
cd ../frontend
npm install
npm run dev
```

**Estado esperable:**
- `http://localhost:5173` — Frontend (login visible, no funcional)
- `http://localhost:8000/docs` — Swagger UI (endpoints visibles, todos retornan null/error)
- `http://localhost:8000/health` — Health check (deberia retornar 200 OK)
- `http://localhost:5000` — MLflow UI (funcional, sin experimentos)

### Opcion C: Backend con mock auth (requiere implementar)

Para que el login funcione de verdad, hay que implementar MINIMO estos 3 archivos:

**1. `backend/app/api/deps.py`** — Validar el JWT del header:
```python
# Flujo: extraer Bearer token → decode_token() → retornar user_id
```

**2. `backend/app/services/auth_service.py`** — Validar credenciales:
```python
# Flujo: buscar usuario por email → verify_password() → create_access_token() + create_refresh_token()
```

**3. `backend/app/api/v1/auth.py`** — Conectar endpoint con servicio:
```python
# Flujo: recibir LoginRequest → AuthService.authenticate() → retornar TokenResponse
```

Adicionalmente, necesitas al menos 1 usuario en la base de datos. Esto se puede hacer con un seed script o una migracion.

---

## 4. DIAGNOSTICO TECNICO DETALLADO

### Que esta bien hecho

1. **Arquitectura del pipeline**: El diseno de 3 etapas (Heuristic → ML → LLM) con el LLM como explicador y NO como tomador de decisiones es una decision de arquitectura excelente. Reduce costos, latencia y riesgo de hallucination.

2. **Modelos de datos**: Los modelos ORM estan bien normalizados. El uso de JSONB para headers, URLs y attachments es correcto — permite schema flexibility sin sacrificar queries SQL.

3. **Schemas Pydantic**: Separacion limpia entre request/response models. Uso correcto de `from_attributes` para ORM compatibility.

4. **Security core**: bcrypt + JWT con tokens separados (access 30min + refresh 7d) es un patron solido. `decode_token()` valida tipo de token correctamente.

5. **Frontend architecture**: Composables (useAuth, useApi, usePagination, useFilters) demuestran buen manejo de Vue 3 Composition API. El service layer con axios interceptors para auth es correcto.

6. **Docker setup**: Multi-stage build, health checks en PostgreSQL, volumes bien definidos. El Makefile simplifica todo el flujo de desarrollo.

### Que necesita atencion

1. **Pipeline helper methods implementados pero no el core**: `orchestrator.py` tiene `_determine_risk_level()` y `_determine_action()` implementados, pero `analyze()` no. Esto sugiere que el diseno esta claro pero la ejecucion no empezo.

2. **Heuristic engine con 4 sub-engines vacios**: `_analyze_domain()`, `_analyze_urls()`, `_analyze_keywords()`, `_analyze_auth()` — todos retornan 0.0. Los TODOs indican la intencion (blacklists, typosquatting, SPF/DKIM/DMARC), pero nada ejecutable.

3. **ML module con guia pero sin codigo**: `train.py` tiene un TODO de 18 lineas que explica exactamente como implementar. El codigo comentado muestra el patron de transformers/HuggingFace. Solo falta escribirlo.

4. **Frontend stores no conectados**: Los stores tienen la estructura correcta pero los metodos `fetch*()` no hacen nada. Esto es coherente — sin backend, no hay API que llamar.

5. **Tests vacios**: Solo `test_security.py` tiene tests reales. Los demas son `pass`. No hay ningun test de integracion funcional.

### Riesgos tecnicos

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| Cold start del modelo ML en produccion | Alto | Alta | Pre-cargar modelo al iniciar Cloud Run |
| LLM timeout (>2s) en pipeline sincrono | Medio | Media | Procesar LLM stage async, no bloquear respuesta |
| JSONB queries lentas sin indices | Medio | Media | Agregar GIN indexes en JSONB columns |
| JWT secret hardcodeado en .env | Critico (si se filtra) | Baja | Usar GCP Secret Manager en produccion |
| Sin rate limiting en API | Alto | Media | Agregar slowapi o middleware custom |

---

## 5. EVALUACION DE HERRAMIENTAS

### 5.1 Autenticacion: JWT (actual) vs Clerk vs Auth0

| Aspecto | JWT (actual) | Clerk | Auth0 |
|---------|-------------|-------|-------|
| **Costo (50 users)** | $0 | $0 | $0 |
| **Costo (500 users)** | $0 | $25/mo | $0 |
| **Integracion FastAPI** | Nativa (python-jose) | Via JWT validation | Via JWT validation |
| **SDK Vue 3** | Custom (axios) | @clerk/vue | @auth0/auth0-vue |
| **Google Workspace SSO** | Custom OAuth2 | Built-in | Built-in |
| **MFA** | Manual (TOTP lib) | Built-in | Built-in |
| **UI de gestion de usuarios** | Hay que construirla | Hosted | Hosted |
| **Setup** | Bajo (ya empezado) | Medio | Medio |
| **Control total** | Si | No | No |
| **Valor academico** | Alto | Bajo | Bajo |
| **Vendor lock-in** | Ninguno | Alto | Alto |
| **Funciona offline** | Si | No | No |

**Recomendacion: MANTENER JWT**

Clerk y Auth0 son overkill para una app single-tenant con <50 usuarios. El JWT ya esta 40% implementado (create/validate tokens funciona). Agregar Clerk no aporta valor academico — es solo integrar un SDK. Implementar auth desde cero demuestra conocimiento de seguridad en la tesis.

### 5.2 Base de datos: PostgreSQL (actual) vs Neon vs Supabase

| Aspecto | PostgreSQL (Docker/GCP) | Neon | Supabase |
|---------|------------------------|------|----------|
| **Costo (10 GB always-on)** | ~$25/mo Cloud SQL | $19/mo | $25/mo |
| **Free tier storage** | Ilimitado (local) | 0.5 GB | 500 MB |
| **Cold start** | Ninguno | ~1-2s (free tier) | ~2-5s (free tier) |
| **Latencia desde GCP** | 1-2ms (misma region) | 5-10ms | 5-10ms |
| **Branching (dev/staging)** | Manual | Git-like branches | Point-in-time recovery |
| **Connection pooling** | PgBouncer manual | Built-in | Built-in (Supavisor) |
| **Desarrollo offline** | Docker Compose | No | No |
| **Integracion GCP** | Nativa (VPC, IAM) | Via internet publico | Via internet publico |
| **SQLAlchemy + Alembic** | Perfecto | Compatible | Compatible |

**Recomendacion: MANTENER POSTGRESQL (Docker local + GCP Cloud SQL produccion)**

Guard-IA procesa emails en tiempo real. No puede tolerar cold starts de 2-5s. Los free tiers de Neon/Supabase (0.5 GB) no alcanzan para artefactos de email + datos de ML. Docker Compose para desarrollo local es superior a depender de internet. GCP Cloud SQL para produccion da backups automaticos, VPC networking y latencia minima.

### 5.3 Storage: Cloudflare R2 vs GCP Cloud Storage vs AWS S3

**Necesidades de storage estimadas:**
- Email attachments: 45-180 GB/trimestre (retencion 90 dias)
- Modelos ML: ~1.5 GB (5 versiones)
- Reportes PDF: ~6 GB/anio
- Logs/artifacts: 10-50 GB/mes (retencion 30 dias)
- **Total anio 1**: 50-250 GB

| Aspecto | Cloudflare R2 | GCP Cloud Storage | AWS S3 |
|---------|--------------|-------------------|--------|
| **Costo storage** | $0.015/GB/mo | $0.020/GB/mo | $0.023/GB/mo |
| **Costo egress** | **$0** | $0.12/GB | $0.09/GB |
| **API compatible S3** | Si | Si (XML API) | Nativo |
| **Free tier** | 10 GB/mo | 5 GB/mo | 5 GB/mo (12 meses) |
| **CDN integrado** | Si (Cloudflare gratis) | Cloud CDN (pago) | CloudFront (pago) |
| **Integracion GCP** | Via internet | Nativa (IAM, VPC) | Via internet |
| **Python SDK** | boto3 (S3 compat) | google-cloud-storage | boto3 |
| **Costo estimado 100 GB** | **~$1.68/mo** | ~$3.40/mo | ~$3.40/mo |

**Recomendacion: CLOUDFLARE R2**

Zero egress fees es la razon principal. En un producto de seguridad, los analistas descargan attachments, reportes y artefactos constantemente. Con GCP/S3, eso se acumula. R2 es S3-compatible (mismo codigo con boto3, solo cambia el endpoint), asi que migrar despues es trivial.

**Estrategia de buckets:**
- `guardia-attachments` — email attachments (lifecycle: 90 dias)
- `guardia-models` — versiones del modelo ML
- `guardia-reports` — reportes PDF de casos (lifecycle: 1 anio)
- `guardia-logs` — trazas LLM para debugging (lifecycle: 30 dias)

### 5.4 Deploy: GCP Cloud Run vs Vercel vs Cloudflare Pages+Workers

| Aspecto | GCP Cloud Run (full) | Vercel + Cloud Run | CF Pages + Workers |
|---------|---------------------|-------------------|-------------------|
| **Frontend** | Cloud Storage + CDN | Vercel | CF Pages |
| **Backend** | Cloud Run | Cloud Run | Workers (JS only!) |
| **Costo frontend** | ~$5/mo | $0 (free tier) | $0 (free tier) |
| **Costo backend** | ~$35/mo | ~$35/mo | ~$5/mo |
| **Preview deploys** | Manual (Cloud Build) | Auto (Git branches) | Auto (Git branches) |
| **Soporte Python** | Si (Docker) | Si (Cloud Run) | **NO** (JS/WASM) |
| **WebSockets** | Si | Si | Limitado |
| **Cold starts** | ~1-2s (min instances: 1) | ~1-2s | ~10-50ms |
| **Vendedores** | 1 (GCP) | 2 (Vercel + GCP) | 1 (CF) |
| **Monitoring** | Unificado (Cloud Logging) | Split (Vercel + GCP) | Split |
| **VPC (DB privado)** | Si | Solo Cloud Run | No |

**Recomendacion: GCP CLOUD RUN PARA TODO**

- **Vercel descartado**: Agregar un vendor mas (Vercel + GCP + R2) crea complejidad innecesaria. CORS, logs split entre plataformas, secrets en 3 lugares distintos. No aporta valor para una tesis.
- **Cloudflare Workers descartado**: No soporta Python. FastAPI requeriria reescritura completa. DistilBERT (250 MB) no entra en el limite de 10 MB de Workers. Las llamadas LLM (2-3s) pueden exceder timeouts.
- **Cloud Run es simple**: Un vendor, un billing, un dashboard de logs. El backend ya tiene Dockerfile listo. El frontend se sirve desde Cloud Storage + Cloud CDN.

**Arquitectura produccion:**
```
Usuario → Cloud Load Balancer (HTTPS)
├── Frontend: Cloud Storage (Vite build) + Cloud CDN
└── Backend: Cloud Run (FastAPI container)
    ├── PostgreSQL: Cloud SQL (IP privada, VPC)
    ├── Storage: Cloudflare R2 (API publica)
    └── APIs: Anthropic (Claude), OpenAI (GPT fallback)
```

---

## 6. STACK RECOMENDADO FINAL

| Componente | Decision | Costo mensual |
|------------|----------|---------------|
| **Auth** | Mantener JWT (python-jose) | $0 |
| **Base de datos** | PostgreSQL (Docker local + GCP Cloud SQL prod) | ~$100 |
| **Storage** | Cloudflare R2 | ~$2 |
| **Deploy backend** | GCP Cloud Run | ~$35 |
| **Deploy frontend** | GCP Cloud Storage + Cloud CDN | ~$5 |
| **Infraestructura total** | | **~$142/mo** |
| **APIs LLM (Claude + GPT)** | | ~$200-500/mo |
| **Total** | | **~$342-642/mo** |

> Nota: los costos de LLM dominan. La infraestructura es <30% del gasto total.

---

## 7. PROXIMOS PASOS SUGERIDOS

### Prioridad 1: Hacer que el login funcione
1. Implementar `AuthService.authenticate()` en `backend/app/services/auth_service.py`
2. Implementar `get_current_user_id()` en `backend/app/api/deps.py`
3. Conectar endpoint `POST /login` en `backend/app/api/v1/auth.py`
4. Crear migration para seed de usuario admin
5. Verificar login end-to-end

### Prioridad 2: Dashboard con datos reales
1. Implementar `DashboardService.get_stats()` con queries a PostgreSQL
2. Conectar `dashboardStore.fetchDashboard()` en el frontend
3. Reemplazar datos mock en los componentes del dashboard

### Prioridad 3: Pipeline core
1. Implementar `HeuristicEngine` (domain, URLs, keywords, auth checks)
2. Implementar `MLClassifier.predict()` con DistilBERT
3. Implementar `LLMExplainer.explain()` con Anthropic API
4. Implementar `PipelineOrchestrator.analyze()` integrando las 3 etapas
5. Conectar con `EmailService.ingest()` y creacion de Cases

### Prioridad 4: Email ingestion
1. Implementar `EmailService.ingest()` (parsear email, guardar artefacto, trigger pipeline)
2. Implementar webhook/polling para Google Workspace
3. Conectar caso completo: email entra → pipeline analiza → caso creado → alerta generada

---

## 8. LO QUE NO HAY QUE HACER

- **No agregar Clerk/Auth0**: No aporta valor para 50 usuarios en single-tenant. Cero aprendizaje academico.
- **No usar Neon/Supabase**: Serverless PostgreSQL es incorrecto para procesamiento de emails en tiempo real. Cold starts rompen la deteccion.
- **No deployar en Vercel**: Complejidad multi-vendor sin beneficio. Un solo vendor (GCP) simplifica todo.
- **No usar AWS S3**: Egress fees se acumulan cuando los analistas descargan. R2 es S3-compatible con $0 egress.
- **No sobre-ingeniar antes de que funcione**: Primero hacer que el login y el pipeline funcionen end-to-end. Despues optimizar.
