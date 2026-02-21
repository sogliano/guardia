# Developer Setup

Guia para levantar Guard-IA en local y empezar a desarrollar.

---

## Prerequisites

- **Python 3.11+** (pyenv recomendado en macOS/Linux, python.org en Windows)
- **Node.js 18+** (nvm recomendado en macOS/Linux, nodejs.org en Windows)
- **Docker** 20+ & Docker Compose (opcional, para base de datos local)
- **Git** 2.30+
- **Make** (pre-installed en macOS/Linux) — **No disponible por defecto en Windows**, usar comandos manuales

---

## Configuración rápida por OS

| | macOS/Linux | Windows |
|--|------------|---------|
| Activar venv | `source .venv/bin/activate` | Usar `.venv\Scripts\python.exe` directamente |
| Setear PYTHONPATH | `PYTHONPATH=$PWD uvicorn ...` | `$env:PYTHONPATH = "." ; .venv\Scripts\uvicorn.exe ...` |
| npm | `npm` | `npm.cmd` (PowerShell bloquea `npm.ps1` con AllSigned) |
| Eliminar directorio | `rm -rf .venv` | `Remove-Item -Recurse -Force .venv` |
| Make | `make dev` | No disponible — usar comandos manuales |

---

## Setup en macOS/Linux

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
python3 -m venv .venv  # Python 3.11+
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"  # Uses pyproject.toml

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

## Setup en Windows (PowerShell)

Esta sección cubre el setup completo en **Windows con PowerShell**. Los comandos de macOS/Linux NO funcionan directamente por diferencias en el shell.

### Problema con PowerShell Execution Policy

Si tu sistema tiene la política `AllSigned`, los scripts `.ps1` (como `npm.ps1` o `.venv\Scripts\Activate.ps1`) no se pueden ejecutar. **Workaround: usar los binarios `.exe` y `.cmd` directamente.**

```powershell
# Ver tu política actual
Get-ExecutionPolicy -List

# Intentar cambiarla (puede estar bloqueada por GPO corporativa)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 1. Backend

```powershell
cd backend

# Crear entorno virtual
python -m venv .venv

# Actualizar pip
.venv\Scripts\python.exe -m pip install --upgrade pip

# Instalar dependencias (base + dev)
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Crear archivo de configuración
Copy-Item .env.example .env
# Editar backend\.env con DB, Clerk, OpenAI, etc.

# Correr migraciones contra la base de datos
$env:PYTHONPATH = "."
.venv\Scripts\alembic.exe upgrade head
```

> **Nota:** Si usás Neon (recomendado para desarrollo), la base de datos ya tiene las migraciones aplicadas.
> `alembic upgrade head` verifica el estado y no hace nada si ya está al día.

### 2. Frontend

```powershell
cd frontend

# Instalar dependencias
npm.cmd install

# Crear archivo de configuración
Copy-Item .env.example .env.local
# Editar frontend\.env.local con VITE_API_BASE_URL y VITE_CLERK_PUBLISHABLE_KEY
```

### 3. Levantar servicios

Abrí **dos terminales PowerShell** separadas:

**Terminal 1 — Backend:**
```powershell
cd backend
$env:PYTHONPATH = "."
.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm.cmd run dev
```

**O con un único terminal usando PowerShell Jobs:**
```powershell
# Reemplazar con tu ruta absoluta real
$root = "C:\Users\TuUsuario\guardia"

$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:root\backend"
    $env:PYTHONPATH = "."
    & "$using:root\backend\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 2>&1
}

$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:root\frontend"
    & "npm.cmd" run dev 2>&1
}

# Verificar que arrancaron (esperar ~5 segundos)
Start-Sleep -Seconds 5
Receive-Job -Id $backendJob.Id | Select-Object -Last 5
Receive-Job -Id $frontendJob.Id | Select-Object -Last 5

# Detener cuando termines
Stop-Job -Id $backendJob.Id, $frontendJob.Id
Remove-Job -Id $backendJob.Id, $frontendJob.Id
```

### 4. Verificar instalación

```powershell
# Backend health (debe retornar {"status":"ok","database":true})
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Select-Object StatusCode, Content

# Frontend
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Select-Object StatusCode
```

### Comandos equivalentes en Windows

| macOS/Linux | Windows PowerShell |
|------------|-------------------|
| `source .venv/bin/activate` | (no necesario — usar `.venv\Scripts\python.exe` directo) |
| `PYTHONPATH=$PWD alembic upgrade head` | `$env:PYTHONPATH = "." ; .venv\Scripts\alembic.exe upgrade head` |
| `PYTHONPATH=$PWD uvicorn app.main:app ...` | `$env:PYTHONPATH = "." ; .venv\Scripts\uvicorn.exe app.main:app ...` |
| `pytest` | `.venv\Scripts\pytest.exe` |
| `ruff check app` | `.venv\Scripts\ruff.exe check app` |
| `npm install` | `npm.cmd install` |
| `npm run dev` | `npm.cmd run dev` |
| `rm -rf .venv` | `Remove-Item -Recurse -Force .venv` |
| `make dev` | Usar comandos manuales (ver arriba) |

### Troubleshooting Windows

**`npm : ... npm.ps1 is not digitally signed`**
```powershell
# Usar npm.cmd en vez de npm
npm.cmd install   # ✅
npm install       # ❌ (falla con AllSigned policy)
```

**`Activate.ps1 cannot be loaded`**
```powershell
# No activar el venv, usar los binarios directamente
.venv\Scripts\python.exe -m pytest   # ✅
source .venv/bin/activate && pytest  # ❌ (sintaxis bash)
```

**`PYTHONPATH=$PWD` no reconocido**
```powershell
# Sintaxis correcta para PowerShell
$env:PYTHONPATH = "."                    # ✅
PYTHONPATH=$PWD uvicorn app.main:app ... # ❌ (sintaxis bash)
```

**Backend no levanta — config no carga**
```powershell
# Verificar que .env existe en backend/
Test-Path "backend\.env"

# Verificar que la config se carga correctamente
cd backend
$env:PYTHONPATH = "."
.venv\Scripts\python.exe -c "from app.config import settings; print('OK:', settings.app_env)"
```

**`make dev` no funciona**
```
'make' is not recognized as an internal or external command
```
Make no viene instalado en Windows. Usar los comandos manuales de las secciones anteriores, o instalar [GNU Make para Windows](https://gnuwin32.sourceforge.net/packages/make.htm) / [Chocolatey: `choco install make`].

---

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
