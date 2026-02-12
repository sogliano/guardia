# Developer Setup

Guia para levantar Guard-IA en local y empezar a desarrollar.

---

## Prerequisites

- **Python 3.11+** (pyenv recomendado)
- **Node.js 18+** (nvm recomendado)
- **Docker** 20+ & Docker Compose
- **Git** 2.30+
- **Make** (pre-installed en macOS/Linux)

### Instalar Python 3.11 (macOS)

```bash
brew install python@3.11
python3.11 --version

# Si no se encuentra, agregar al PATH:
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Instalar Node.js 18+ (nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc
nvm install 18
nvm use 18
```

---

## Setup Inicial

### 1. Clone & Configure

```bash
git clone https://github.com/sogliano/guardia.git
cd guardia
```

### 2. Database

**Docker (recomendado):**
```bash
docker-compose up -d db
```

**PostgreSQL local:**
```bash
psql -h localhost -U $(whoami) postgres << EOF
CREATE DATABASE guardia;
CREATE USER guardia WITH PASSWORD 'guardia_dev';
ALTER DATABASE guardia OWNER TO guardia;
GRANT ALL PRIVILEGES ON DATABASE guardia TO guardia;
EOF
```

### 3. Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Environment
cp .env.example .env
# Editar .env con:
#   DATABASE_URL, CLERK_PEM_PUBLIC_KEY, OPENAI_API_KEY
#   GOOGLE_SERVICE_ACCOUNT_JSON (opcional, para Gmail API delivery)
#   GATEWAY_INTERNAL_TOKEN (opcional, habilita Internal API :8025)

# Migrations
PYTHONPATH=$PWD alembic upgrade head
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Editar .env.local con:
#   VITE_API_BASE_URL=http://localhost:8000/api/v1
#   VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

---

## Levantar Aplicacion

### Opcion 1: Make (recomendado)

```bash
make dev
# Inicia: PostgreSQL (:5432), MLflow (:5000), Backend (:8000), Frontend (:3000)
```

### Opcion 2: Manual (2 terminales)

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
PYTHONPATH=$PWD uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### URLs

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| MLflow | http://localhost:5000 |

---

## Verificar Instalacion

```bash
# Backend health
curl http://localhost:8000/health

# Frontend: abrir http://localhost:3000

# Tests
cd backend && pytest
cd frontend && npm run test
```

---

## Development Workflow

### Branches

```
feat/feature-name    - nueva feature
fix/bug-name         - bug fix
docs/doc-name        - documentacion
refactor/what        - refactoring
```

### Ciclo de desarrollo

```bash
git checkout main && git pull
git checkout -b feat/my-feature

# Desarrollar...
make lint    # ruff + mypy + eslint
make test    # pytest + vitest

git add <files>
git commit -m "add status filter to cases endpoint"
git push origin feat/my-feature
# Crear PR en GitHub
```

### Coding Standards

Seguir los patrones definidos en [CLAUDE.md](../CLAUDE.md):
- **Backend:** Python async, 4 spaces, type hints, structlog, coverage >= 60%
- **Frontend:** Vue 3 `<script setup lang="ts">`, 2 spaces, Pinia, coverage >= 30%

---

## Ingestar Email de Prueba

```bash
# Via script
cd backend
python scripts/simulate_email.py

# Via UI
# 1. Abrir http://localhost:3000
# 2. Login con Clerk
# 3. Ir a Monitoring > Ingest Email
```

---

## Make Commands

```bash
make dev              # Start all services
make test             # Run all tests
make lint             # ruff + mypy + eslint
make migrate          # Run Alembic migrations
make migration msg="" # Create new migration
make train-ml         # Train ML model
make simulate-email   # Send test email
```

---

## SQL Logs

```bash
# Ver queries SQL (debugging):
APP_ENV=local APP_DEBUG=true

# Logs limpios (desarrollo normal):
APP_ENV=local APP_DEBUG=false
```

---

## Troubleshooting

### "relation does not exist"
```bash
cd backend && PYTHONPATH=$PWD alembic upgrade head
```

### "database is being accessed by other users"
```bash
psql -h localhost -U $(whoami) postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'guardia' AND pid <> pg_backend_pid();"
psql -h localhost -U $(whoami) postgres -c "DROP DATABASE guardia; CREATE DATABASE guardia; ALTER DATABASE guardia OWNER TO guardia;"
cd backend && PYTHONPATH=$PWD alembic upgrade head
```

### "401 Unauthorized"
Verificar `CLERK_PEM_PUBLIC_KEY` en `backend/.env`.

### "CORS policy"
Verificar `CORS_ORIGINS=http://localhost:3000,http://localhost:5173` en `backend/.env`.

### Frontend queda en "Loading..."
1. Verificar backend: `curl http://localhost:8000/health`
2. Verificar auth en DevTools > Network
3. Verificar datos en DB (ingestar email de prueba)

### Recrear DB desde cero
```bash
lsof -ti:8000 | xargs kill
psql -h localhost -U $(whoami) postgres -c "DROP DATABASE IF EXISTS guardia; CREATE DATABASE guardia; ALTER DATABASE guardia OWNER TO guardia;"
cd backend && PYTHONPATH=$PWD alembic upgrade head
```

---

## Checklist Rapido

- [ ] PostgreSQL corriendo
- [ ] BD `guardia` creada + migraciones ejecutadas
- [ ] `backend/.env` configurado (Clerk, OpenAI, DB)
- [ ] `frontend/.env.local` configurado (API URL, Clerk key)
- [ ] Backend corriendo en :8000
- [ ] Frontend corriendo en :3000
- [ ] Login funciona en http://localhost:3000
