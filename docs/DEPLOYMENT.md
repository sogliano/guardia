# Guard-IA — Deployment Guide

> Guia completa para configurar staging y production desde cero.

---

## Arquitectura de Ambientes

```
STAGING                                    PRODUCTION
───────────────────────                    ───────────────────────
Frontend: Vercel                           Frontend: Vercel
  Project: guardia-staging                   Project: guardia-production
  URL: guardia-staging.vercel.app            URL: guardia.vercel.app

Backend: Cloud Run                         Backend: Cloud Run
  Service: guardia-api-staging               Service: guardia-api-production
  Region: us-east1                           Region: us-east1

DB: Neon PostgreSQL                        DB: Neon PostgreSQL
  Branch: staging                            Branch: main

Registry: Artifact Registry               (shared)
  Repo: guardia                              Tags: staging-<sha>, prod-<sha>
```

---

## PASO 1: Vercel — Crear Proyectos desde Cero

### 1.1 Limpiar proyectos viejos

Si tenes proyectos anteriores (ej: "guardia-staging-7jpfvd6ht-nicos-projects..."), eliminalos:

1. Vercel Dashboard > seleccionar el proyecto viejo
2. Settings > General > scroll al fondo > **Delete Project**

### 1.2 Crear proyecto STAGING

1. Vercel Dashboard > **Add New... > Project**
2. Seleccionar **Import Git Repository** > tu repo `guardia`
3. Configurar:
   - **Project Name:** `guardia-staging`
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. **Environment Variables** (agregar estas):
   - `VITE_CLERK_PUBLISHABLE_KEY` = tu publishable key de Clerk
   - `VITE_API_BASE_URL` = `https://guardia-api-staging-XXXXXXX.us-east1.run.app` (la URL de tu Cloud Run staging)
5. Click **Deploy**
6. Una vez creado, ir a **Settings > General** y anotar:
   - **Project ID** (es un string tipo `prj_xxxxxxxxxxxxxxxxxxxx`)
7. Ir a **Settings > Domains** y agregar: `guardia-staging.vercel.app` (si no esta ya)
8. **IMPORTANTE:** Ir a **Settings > Git** y **desconectar el repositorio** (Disconnect). Queremos que SOLO el GitHub Action haga deploys, no que Vercel haga auto-deploy en cada push.

> **Nota:** Vercel NO buildea el frontend. GitHub Actions ejecuta `npm run build` (Vite) inyectando `VITE_API_BASE_URL` y `VITE_CLERK_PUBLISHABLE_KEY` desde GitHub environment secrets, y sube el directorio `dist/` pre-compilado via `vercel deploy --prod --yes dist/`. Las env vars del dashboard de Vercel no se usan en el build.

### 1.3 Crear proyecto PRODUCTION

Repetir exactamente lo mismo pero con:

- **Project Name:** `guardia-production`
- **Environment Variables:**
  - `VITE_CLERK_PUBLISHABLE_KEY` = tu publishable key de Clerk (puede ser la misma o una de produccion)
  - `VITE_API_BASE_URL` = `https://guardia-api-production-XXXXXXX.us-east1.run.app`
- Anotar el **Project ID** del proyecto production
- **Desconectar Git** igual que staging

### 1.4 Obtener IDs y Token

Ahora tenes que anotar estos valores:

| Valor | Donde encontrarlo |
|-------|-------------------|
| **VERCEL_TOKEN** | vercel.com > Account Settings (tu avatar arriba a la derecha) > Tokens > Create |
| **VERCEL_ORG_ID** | vercel.com > Team Settings > General > Team ID (`team_xxxx...`) |
| **VERCEL_STAGING_PROJECT_ID** | Vercel > guardia-staging > Settings > General > Project ID |
| **VERCEL_PRODUCTION_PROJECT_ID** | Vercel > guardia-production > Settings > General > Project ID |

---

## PASO 2: Google Cloud — Artifact Registry + Cloud Run

### 2.1 Crear Artifact Registry (una sola vez)

```bash
gcloud auth login
gcloud config set project gen-lang-client-0127131422

# Crear repositorio Docker
gcloud artifacts repositories create guardia \
  --repository-format=docker \
  --location=us-east1 \
  --description="Guard-IA Docker images"
```

Si ya existe, este comando va a fallar con "already exists" — esta bien, seguir adelante.

### 2.2 Crear servicio Cloud Run STAGING

```bash
# Primera vez: crear servicio con imagen placeholder
gcloud run deploy guardia-api-staging \
  --image=us-east1-docker.pkg.dev/gen-lang-client-0127131422/guardia/guardia-api:latest \
  --region=us-east1 \
  --platform=managed \
  --port=8000 \
  --memory=4Gi \
  --cpu=2 \
  --cpu-boost \
  --min-instances=0 \
  --max-instances=2 \
  --timeout=300 \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=staging"
```

> Nota: La primera vez puede fallar si no hay imagen todavia. Eso se resuelve al correr el workflow.

### 2.3 Crear servicio Cloud Run PRODUCTION

```bash
gcloud run deploy guardia-api-production \
  --image=us-east1-docker.pkg.dev/gen-lang-client-0127131422/guardia/guardia-api:latest \
  --region=us-east1 \
  --platform=managed \
  --port=8000 \
  --memory=4Gi \
  --cpu=2 \
  --cpu-boost \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300 \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=production"
```

### 2.4 Configurar Environment Variables en Cloud Run

Para cada servicio (staging y production), configurar las env vars:

```bash
# STAGING
gcloud run services update guardia-api-staging \
  --region=us-east1 \
  --set-env-vars="\
APP_ENV=staging,\
APP_DEBUG=false,\
DATABASE_URL=postgresql+asyncpg://...(tu URL Neon staging),\
CLERK_SECRET_KEY=sk_test_...,\
CLERK_PUBLISHABLE_KEY=pk_test_...,\
CLERK_PEM_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...,\
OPENAI_API_KEY=sk-proj-...,\
OPENAI_MODEL=gpt-4o-mini,\
CORS_ORIGINS=https://guardia-staging.vercel.app,\
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...,\
FRONTEND_BASE_URL=https://guardia-staging.vercel.app,\
ACCEPTED_DOMAINS=strike.sh,\
GATEWAY_API_URL=http://INTERNAL_IP:8025,\
GATEWAY_INTERNAL_TOKEN=<shared-secret>"
```

```bash
# PRODUCTION (similar pero con valores de produccion)
gcloud run services update guardia-api-production \
  --region=us-east1 \
  --set-env-vars="\
APP_ENV=production,\
APP_DEBUG=false,\
DATABASE_URL=postgresql+asyncpg://...(tu URL Neon production),\
CLERK_SECRET_KEY=sk_live_...,\
CLERK_PUBLISHABLE_KEY=pk_live_...,\
OPENAI_API_KEY=sk-proj-...,\
OPENAI_MODEL=gpt-4o,\
CORS_ORIGINS=https://guardia.vercel.app,\
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...,\
FRONTEND_BASE_URL=https://guardia.vercel.app,\
ACCEPTED_DOMAINS=strike.sh,\
GATEWAY_API_URL=http://INTERNAL_IP:8025,\
GATEWAY_INTERNAL_TOKEN=<shared-secret>"
```

> Tip: Tambien podes configurar env vars desde la Google Cloud Console (Cloud Run > tu servicio > Edit & Deploy New Revision > Variables & Secrets).

### 2.5 Service Account para GitHub Actions

Ya tenes la service account `81580052566-compute@developer.gserviceaccount.com`. Asegurate que tenga estos roles:

1. Google Cloud Console > IAM & Admin > IAM
2. Buscar `81580052566-compute@developer.gserviceaccount.com`
3. Editar y agregar roles:
   - **Cloud Run Admin** (`roles/run.admin`)
   - **Artifact Registry Writer** (`roles/artifactregistry.writer`)
   - **Service Account User** (`roles/iam.serviceAccountUser`)

---

## PASO 3: GitHub Secrets

Ir a tu repo en GitHub > **Settings > Secrets and variables > Actions**.

### 3.1 Repository Secrets (compartidos)

| Secret | Valor |
|--------|-------|
| `GCP_PROJECT_ID` | `gen-lang-client-0127131422` |
| `GCP_SA_KEY` | El JSON completo de la service account |
| `VERCEL_TOKEN` | El token que creaste en Vercel |
| `VERCEL_ORG_ID` | `team_ngBtqsNkGq3hBWT7Art79GPA` |
| `VITE_CLERK_PUBLISHABLE_KEY` | Tu Clerk publishable key |
| `HF_TOKEN` | HuggingFace token (para modelo ML privado) |

### 3.2 Environment Secrets (por ambiente)

Ir a **Settings > Environments** y crear dos environments:

#### Environment: `staging`

| Secret | Valor |
|--------|-------|
| `VERCEL_PROJECT_ID` | El Project ID del proyecto `guardia-staging` en Vercel |
| `VITE_API_BASE_URL` | `https://guardia-api-staging-81580052566.us-east1.run.app/api/v1` |

#### Environment: `production`

| Secret | Valor |
|--------|-------|
| `VERCEL_PROJECT_ID` | El Project ID del proyecto `guardia-production` en Vercel |
| `VITE_API_BASE_URL` | `https://guardia-api-production-XXXXX.us-east1.run.app/api/v1` |

> **IMPORTANTE:** `VITE_API_BASE_URL` DEBE estar como **environment secret** (no repo secret), porque el workflow usa `environment: staging/production` y el valor difiere por ambiente. Si no esta configurado, el frontend hace requests a `localhost:8000` (fallback en `api.ts`).

Opcionalmente en `production` podes agregar:
- **Required reviewers** — para que alguien apruebe antes de deployar
- **Branch protection** — el workflow ya valida que sea `main`, pero esto es defensa extra

---

## PASO 4: Ejecutar Deploys

### Deploy Staging

1. GitHub > Actions > **Deploy Staging**
2. Click **Run workflow**
3. Seleccionar el branch (cualquiera)
4. Click **Run workflow** (boton verde)

El workflow automaticamente:
- Corre tests con coverage >= 60%
- Buildea y pushea imagen Docker a Artifact Registry
- Deploya a Cloud Run staging
- Sincroniza la VM SMTP Gateway (git pull del branch seleccionado + restart servicio)

### Deploy Production

1. GitHub > Actions > **Deploy Production**
2. Click **Run workflow**
3. **Solo funciona con branch `main`** — cualquier otro branch es rechazado automaticamente
4. Click **Run workflow**

El workflow automaticamente:
- Valida que sea branch `main`
- Corre tests con coverage >= 60%
- Descarga modelo ML desde HuggingFace
- Buildea y pushea imagen Docker a Artifact Registry
- Deploya a Cloud Run production
- Sincroniza la VM SMTP Gateway (git pull + restart servicio)

### Deploy Frontend

El frontend tiene workflows separados: **Deploy Frontend Staging** y **Deploy Frontend Production**.

1. GitHub > Actions > **Deploy Frontend Staging** (o Production)
2. Click **Run workflow**

El workflow automaticamente:
- Corre tests unitarios (Vitest)
- Buildea con Vite inyectando `VITE_API_BASE_URL` y `VITE_CLERK_PUBLISHABLE_KEY` desde GitHub environment secrets
- Deploya `dist/` a Vercel via `vercel deploy --prod --yes dist/`

### Resumen de Workflows (5 total)

| Workflow | Archivo | Trigger |
|----------|---------|---------|
| CI | `ci.yml` | Automatico en PRs a `main` |
| Deploy Backend Staging | `deploy-backend-staging.yml` | Manual (cualquier branch) |
| Deploy Backend Production | `deploy-backend-production.yml` | Manual (solo `main`) |
| Deploy Frontend Staging | `deploy-frontend-staging.yml` | Manual |
| Deploy Frontend Production | `deploy-frontend-production.yml` | Manual |

---

## PASO 5: Verificar

### Frontend
- Staging: `https://guardia-staging.vercel.app`
- Production: `https://guardia.vercel.app` (o el dominio que configures)

### Backend
- Staging: `https://guardia-api-staging-XXXXX.us-east1.run.app/health`
- Production: `https://guardia-api-production-XXXXX.us-east1.run.app/health`

### Checklist de verificacion
- [ ] Frontend carga sin errores en consola
- [ ] Login con Clerk funciona
- [ ] Dashboard muestra datos
- [ ] `/health` del backend responde 200
- [ ] CORS no bloquea requests del frontend al backend

---

## Resumen de Nombres

| Recurso | Staging | Production |
|---------|---------|------------|
| Vercel Project | `guardia-staging` | `guardia-production` |
| Vercel URL | `guardia-staging.vercel.app` | `guardia.vercel.app` |
| Cloud Run Service | `guardia-api-staging` | `guardia-api-production` |
| Cloud Run Region | `us-east1` | `us-east1` |
| Docker Image Tag | `staging-<sha>` | `prod-<sha>` |
| Artifact Registry | `us-east1-docker.pkg.dev/gen-lang-client-0127131422/guardia/guardia-api` |
| GCP Project | `gen-lang-client-0127131422` |
| GitHub Environment | `staging` | `production` |
| GitHub Workflow | Deploy Staging | Deploy Production |
| Neon DB | `guardia_test` (staging branch) | `guardia` (main branch) |
