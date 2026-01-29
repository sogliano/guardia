# Guard-IA

**Sistema middleware de detección de fraude en correos electrónicos corporativos, potenciado por inteligencia artificial.**

Guard-IA es un sistema de intercepción pre-entrega que analiza emails en tiempo real mediante un pipeline de 3 etapas, integrándose con Google Workspace como middleware SMTP. Desarrollado como proyecto de tesis en la Universidad ORT Uruguay para Strike Security.

---

## Arquitectura

```
                    ┌──────────────┐
                    │   Google     │
                    │  Workspace   │
                    └──────┬───────┘
                           │ SMTP
                    ┌──────▼───────┐
                    │ SMTP Gateway │ :2525
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │    Detection Pipeline   │
              │                         │
              │  1. Heuristic Engine    │ ~5ms
              │     SPF/DKIM/DMARC     │
              │     Domain reputation  │
              │     URL analysis       │
              │     Urgency patterns   │
              │                         │
              │  2. ML Classifier      │ ~18ms
              │     DistilBERT (66M)   │
              │     Fine-tuned         │
              │                         │
              │  3. LLM Explainer      │ ~2-3s
              │     Claude / GPT-4.1   │
              │     Explicación only   │
              └────────────┬────────────┘
                           │
                    ┌──────▼───────┐
                    │   Decisión   │
                    │              │
                    │ < 0.3  ALLOW │
                    │ 0.3-0.6 WARN │
                    │ ≥ 0.8  QUAR. │
                    └──────────────┘
```

### Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.11+ · FastAPI · SQLAlchemy Async · Pydantic v2 |
| **Frontend** | Vue 3 · TypeScript · Pinia · Chart.js · Vite |
| **Base de datos** | PostgreSQL 16 (JSONB para metadata de emails) |
| **ML** | DistilBERT fine-tuned · MLflow |
| **LLM** | Claude Opus 4.5 (primario) · GPT-4.1 (fallback) |
| **Auth** | Clerk (RS256 JWT, invitation-only) |
| **Infra** | Docker · Nginx · GCP |
| **Gateway** | Servidor SMTP custom (puerto 2525) |

---

## Estructura del Proyecto

```
guardia/
├── backend/                 # API REST + Pipeline de detección
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST
│   │   ├── services/        # Lógica de negocio
│   │   │   └── pipeline/    # Motor de detección (heuristics, ML, LLM)
│   │   ├── models/          # Modelos SQLAlchemy (16 entidades)
│   │   ├── schemas/         # Schemas Pydantic v2
│   │   ├── gateway/         # Interceptor SMTP
│   │   ├── core/            # Constantes, seguridad, excepciones
│   │   └── db/              # Sesión async + migraciones Alembic
│   └── tests/
├── frontend/                # SPA Dashboard
│   └── src/
│       ├── views/           # 12 vistas (Dashboard, Cases, Quarantine, etc.)
│       ├── components/      # Componentes reutilizables
│       ├── stores/          # Pinia stores
│       ├── services/        # Clientes HTTP (Axios)
│       └── types/           # Interfaces TypeScript
├── ml/                      # Modelo DistilBERT
│   ├── src/                 # Train, evaluate, predict, preprocess
│   ├── models/              # Modelo pre-entrenado
│   ├── notebooks/           # Notebooks de exploración
│   └── data/                # Datasets (raw/processed)
├── infra/                   # Docker, GCP, scripts
├── docs/                    # Documentación del proyecto
├── docker-compose.yml       # Orquestación de servicios
└── Makefile                 # Comandos de desarrollo
```

---

## Quick Start

### Requisitos previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 16
- Docker & Docker Compose

### Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd guardia

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales necesarias

# 3. Setup completo (entorno, dependencias, Docker, migraciones)
make setup

# 4. Iniciar todos los servicios
make dev
```

### Servicios en desarrollo

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Dashboard SPA |
| Backend API | http://localhost:8000/api/v1 | REST API |
| PostgreSQL | localhost:5432 | Base de datos |
| MLflow | http://localhost:5000 | Tracking de modelos |
| SMTP Gateway | localhost:2525 | Interceptor de emails |

---

## Comandos de Desarrollo

```bash
# Servidores
make dev                  # Iniciar backend + frontend + DB
make dev-all              # Incluye SMTP gateway
make dev-gateway          # Solo gateway SMTP

# Testing
make test                 # Todos los tests
make test-backend         # Solo backend (pytest)
make test-frontend        # Solo frontend (vitest)

# Code quality
make lint                 # Todos los linters
make lint-backend         # ruff + mypy
make lint-frontend        # eslint

# Base de datos
make migrate              # Ejecutar migraciones pendientes
make migration msg="..."  # Crear nueva migración

# ML
make train-model          # Entrenar modelo
make evaluate-model       # Evaluar modelo

# Docker
make up / down / build    # Operaciones Docker Compose

# Simulación
make simulate             # Simular tráfico de emails
```

---

## Pipeline de Detección

El pipeline procesa cada email en 3 etapas secuenciales:

### Etapa 1: Motor Heurístico (~5ms)
Reglas determinísticas que evalúan:
- **Autenticación**: SPF, DKIM, DMARC
- **Dominio**: Reputación, typosquatting, TLDs sospechosos
- **URLs**: Acortadores, IPs directas, mismatches
- **Contenido**: Patrones de urgencia, phishing keywords

### Etapa 2: Clasificador ML (~18ms)
- Modelo `distilbert-base-uncased` fine-tuned (66M parámetros)
- Entrenado con dataset de emails corporativos
- Output: score de riesgo (0.0 - 1.0) + confianza

### Etapa 3: Explicador LLM (~2-3s)
- Claude Opus 4.5 (primario), GPT-4.1 (fallback)
- Genera explicación en lenguaje natural
- **No toma decisiones**, solo explica el análisis

### Score Final
Combinación ponderada: **Heurístico (40%) + ML (60%)**

| Score | Acción |
|-------|--------|
| < 0.3 | Allow — Email entregado normalmente |
| 0.3 - 0.6 | Warn — Entregado con advertencia |
| ≥ 0.8 | Quarantine — Retenido para revisión manual |

---

## Modelo de Datos

```
┌─────────────┐     ┌──────────┐     ┌────────────┐
│   emails    │────▶│  cases   │────▶│  analyses  │
│             │     │          │     │ (per stage)│
│ sender      │     │ status   │     │ score      │
│ recipient   │     │ verdict  │     │ confidence │
│ subject     │     │ risk     │     │ explanation│
│ body        │     │ score    │     └─────┬──────┘
│ headers     │     └────┬─────┘           │
│ auth_results│          │           ┌─────▼──────┐
└─────────────┘          │           │ evidences  │
                         │           │ (signals)  │
                    ┌────▼─────┐     └────────────┘
                    │  notes   │
                    │fp_reviews│
                    │quarantine│
                    │ actions  │
                    └──────────┘
```

### Entidades principales
- **emails** — Artefactos del email original (headers, URLs, auth como JSONB)
- **cases** — Contenedor de análisis por email
- **analyses** — Resultado por etapa del pipeline (heuristic/ml/llm)
- **evidences** — Señales individuales de detección
- **case_notes** — Notas del analista
- **fp_reviews** — Revisiones de falsos positivos
- **alert_rules / alert_events** — Sistema de alertas configurables
- **policy_entries** — Whitelists/blacklists

---

## Dashboard

El dashboard proporciona visibilidad completa del estado de seguridad:

- **KPIs**: Emails analizados, amenazas detectadas, bloqueados/cuarentenados, tiempo de respuesta
- **Threat Trend**: Tendencia diaria de amenazas (últimos 30 días)
- **Risk Distribution**: Distribución de niveles de riesgo (doughnut chart)
- **Verdict Timeline**: Evolución temporal de veredictos (stacked area)
- **Threat Categories**: Desglose por tipo de amenaza (horizontal bar)
- **Score Distribution**: Histograma de scores con umbrales visuales
- **Recent Cases**: Últimos casos analizados
- **Pipeline Health**: Métricas de rendimiento del pipeline

---

## Configuración

### Variables de entorno principales

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/guardia

# Autenticación (Clerk)
CLERK_SECRET_KEY=sk_...
CLERK_PUBLISHABLE_KEY=pk_...
CLERK_PEM_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...

# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# SMTP Gateway
SMTP_HOST=0.0.0.0
SMTP_PORT=2525
GOOGLE_RELAY_HOST=smtp-relay.gmail.com

# Pipeline
PIPELINE_THRESHOLD_ALLOW=0.3
PIPELINE_THRESHOLD_WARN=0.6
PIPELINE_THRESHOLD_QUARANTINE=0.8
```

Ver `.env.example` para la lista completa de variables.

---

## Contexto Académico

Este proyecto es una tesis de grado de la Universidad ORT Uruguay, desarrollado para Strike Security. Las decisiones técnicas, la evolución de la arquitectura y los cambios en el ciclo de vida del sistema tienen peso académico significativo.

**Autor**: Strike Security
**Universidad**: ORT Uruguay
**Tipo**: Tesis de grado — Ingeniería en Sistemas
