# Guard-IA — Infrastructure Reference

> Documento centralizado con todas las URLs, credenciales, servicios y configuraciones de la infraestructura.

---

## Servicios y URLs

### Google Cloud Platform

| Recurso | Valor |
|---------|-------|
| **GCP Project ID** | `gen-lang-client-0127131422` |
| **Region** | `us-east1` |
| **Service Account** | `81580052566-compute@developer.gserviceaccount.com` |
| **Roles asignados** | `roles/editor`, `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser` |

#### Artifact Registry

| Recurso | Valor |
|---------|-------|
| **Repository** | `guardia` |
| **Format** | Docker |
| **Location** | `us-east1` |
| **Full path** | `us-east1-docker.pkg.dev/gen-lang-client-0127131422/guardia` |

#### Cloud Run — Staging

| Recurso | Valor |
|---------|-------|
| **Service name** | `guardia-api-staging` |
| **URL** | `https://guardia-api-staging-81580052566.us-east1.run.app` |
| **Health** | `https://guardia-api-staging-81580052566.us-east1.run.app/health` |
| **CPU / Memory** | 1 CPU / 2 GiB |
| **Instances** | 0-2 (scale to zero) |
| **Timeout** | 300s |

#### Cloud Run — Production

| Recurso | Valor |
|---------|-------|
| **Service name** | `guardia-api-production` |
| **URL** | `https://guardia-api-production-81580052566.us-east1.run.app` |
| **Health** | `https://guardia-api-production-81580052566.us-east1.run.app/health` |
| **CPU / Memory** | 1 CPU / 2 GiB |
| **Instances** | 0-3 (scale to zero) |
| **Timeout** | 300s |

#### Cloud Run — Legacy (eliminar cuando se confirme que no se usa)

| Recurso | Valor |
|---------|-------|
| **Service name** | `guardia-api` |
| **URL** | `https://guardia-api-81580052566.us-east1.run.app` |

---

### Vercel (Frontend)

| Recurso | Staging | Production |
|---------|---------|------------|
| **Project name** | `guardia-staging` | `guardia-production` |
| **Project ID** | `(completar: prj_...)` | `(completar: prj_...)` |
| **URL** | `https://guardia-staging.vercel.app` | `https://guardia-production.vercel.app` |
| **Framework** | Vite | Vite |
| **Root directory** | `frontend` | `frontend` |
| **Build command** | `npm run build` | `npm run build` |
| **Output directory** | `dist` | `dist` |
| **Git connected** | No (deploy via GitHub Action) | No (deploy via GitHub Action) |

| Config general | Valor |
|----------------|-------|
| **Team name** | Guard-IA |
| **Team URL** | `vercel.com/guard-ia` |
| **Team ID (ORG_ID)** | `team_ngBtqsNkGq3hBWT7Art79GPA` |
| **Token** | `Bm5UsX1HECkhZARvBTDliqhI` |

---

### Neon (PostgreSQL)

| Recurso | Staging | Production |
|---------|---------|------------|
| **Database** | `guardia_test` | `guardia` (pendiente crear) |
| **Region** | `sa-east-1` | `sa-east-1` |
| **Connection string** | `postgresql+asyncpg://neondb_owner:npg_pY2oVFBWd1Ie@ep-raspy-boat-ack7fwto-pooler.sa-east-1.aws.neon.tech/guardia_test?sslmode=require` | `(completar)` |
| **Console** | [console.neon.tech](https://console.neon.tech) | |

---

### Clerk (Authentication)

| Recurso | Staging (Test) | Production (Live) |
|---------|----------------|-------------------|
| **Publishable Key** | `pk_test_c2VjdXJlLXRlcnJhcGluLTUwLmNsZXJrLmFjY291bnRzLmRldiQ` | `(completar)` |
| **Secret Key** | `sk_test_7bqlW36YKQDjekg3RVzhbLfTD5qtX9w0CYJohDi1z4` | `(completar)` |
| **Mode** | Invitation-only | Invitation-only |
| **Console** | [dashboard.clerk.com](https://dashboard.clerk.com) | |

---

### LLM Providers

| Provider | Staging | Production |
|----------|---------|------------|
| **OpenAI (staging)** | `gpt-4o-mini` | `gpt-4.1` |
| **OpenAI API Key** | `sk-proj-fNd9...ZKVsA` | `(misma)` |

---

### Slack (Alerts)

| Recurso | Valor |
|---------|-------|
| **Webhook URL** | `(configurado — ver Slack App settings)` |
| **Usado en** | Staging + Production |

---

## GitHub Actions

### Workflows

| Workflow | Archivo | Trigger | Branch restriction |
|----------|---------|---------|-------------------|
| Deploy Staging | `.github/workflows/deploy-staging.yml` | Manual (workflow_dispatch) | Cualquier branch |
| Deploy Production | `.github/workflows/deploy-production.yml` | Manual (workflow_dispatch) | Solo `main` |

### GitHub Secrets (Repository-level)

| Secret | Valor | Estado |
|--------|-------|--------|
| `GCP_PROJECT_ID` | `gen-lang-client-0127131422` | Pendiente agregar |
| `GCP_SA_KEY` | JSON de service account | Pendiente agregar |
| `VERCEL_TOKEN` | `Bm5UsX1HECkhZARvBTDliqhI` | Pendiente agregar |
| `VERCEL_ORG_ID` | `team_ngBtqsNkGq3hBWT7Art79GPA` | Pendiente agregar |
| `VITE_CLERK_PUBLISHABLE_KEY` | `pk_test_c2Vjd...` | Pendiente agregar |

### GitHub Environment Secrets

| Environment | Secret | Valor | Estado |
|-------------|--------|-------|--------|
| `staging` | `VERCEL_PROJECT_ID` | `(completar: prj_...)` | Pendiente crear |
| `production` | `VERCEL_PROJECT_ID` | `(completar: prj_...)` | Pendiente crear |

---

## Environment Variables por Servicio

### Cloud Run — Staging (guardia-api-staging)

| Variable | Valor | Configurado |
|----------|-------|-------------|
| `APP_ENV` | `staging` | Si |
| `APP_DEBUG` | `false` | Si |
| `DATABASE_URL` | `postgresql+asyncpg://...guardia_test?sslmode=require` | Si |
| `CLERK_SECRET_KEY` | `sk_test_...` | Si |
| `CLERK_PUBLISHABLE_KEY` | `pk_test_...` | Si |
| `CLERK_PEM_PUBLIC_KEY` | PEM key (configurar via Console) | **Pendiente** |
| `OPENAI_API_KEY` | `sk-proj-...` | Si |
| `OPENAI_MODEL` | `gpt-4o-mini` | Si |
| `PIPELINE_ML_ENABLED` | `false` | Si |
| `CORS_ORIGINS` | `https://guardia-staging.vercel.app` | Si |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Si |
| `FRONTEND_BASE_URL` | `https://guardia-staging.vercel.app` | Si |
| `ACCEPTED_DOMAINS` | `strike.sh` | Si |

### Cloud Run — Production (guardia-api-production)

| Variable | Valor | Configurado |
|----------|-------|-------------|
| `APP_ENV` | `production` | **Pendiente** |
| `APP_DEBUG` | `false` | **Pendiente** |
| `DATABASE_URL` | `(Neon production URL)` | **Pendiente** |
| `CLERK_SECRET_KEY` | `sk_live_...` | **Pendiente** |
| `CLERK_PUBLISHABLE_KEY` | `pk_live_...` | **Pendiente** |
| `CLERK_PEM_PUBLIC_KEY` | PEM key | **Pendiente** |
| `OPENAI_API_KEY` | `sk-proj-...` | **Pendiente** |
| `OPENAI_MODEL` | `gpt-4.1` | **Pendiente** |
| `PIPELINE_ML_ENABLED` | `true` | **Pendiente** |
| `CORS_ORIGINS` | `https://guardia-production.vercel.app` | **Pendiente** |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | **Pendiente** |
| `FRONTEND_BASE_URL` | `https://guardia-production.vercel.app` | **Pendiente** |
| `ACCEPTED_DOMAINS` | `strike.sh` | **Pendiente** |

---

## Pendientes de configurar

- [ ] Crear proyecto `guardia-staging` en Vercel y anotar Project ID
- [ ] Crear proyecto `guardia-production` en Vercel y anotar Project ID
- [ ] Desconectar Git de ambos proyectos Vercel
- [ ] Configurar `CLERK_PEM_PUBLIC_KEY` en Cloud Run staging (via Console)
- [ ] Configurar todas las env vars de Cloud Run production
- [ ] Agregar 5 repository secrets en GitHub
- [ ] Crear environment `staging` en GitHub con `VERCEL_PROJECT_ID`
- [ ] Crear environment `production` en GitHub con `VERCEL_PROJECT_ID`
- [ ] Crear base de datos de production en Neon
- [ ] Obtener Clerk live keys para production
- [ ] Primer deploy staging via GitHub Action
- [ ] Primer deploy production via GitHub Action
- [ ] Eliminar servicio legacy `guardia-api` de Cloud Run cuando ya no se use
