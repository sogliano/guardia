# 🚀 Levantar Guard-IA en Local

Instrucciones para correr el proyecto completo en desarrollo local con logs en tiempo real.

---

## ✅ Pre-requisitos

Antes de empezar, asegúrate de tener:

- **PostgreSQL** corriendo (puerto 5432)
- **Base de datos** `guardia` creada con owner `guardia`
- **Python 3.11+** con virtualenv en `backend/.venv`
- **Node.js 18+** con dependencias instaladas en `frontend/`

---

## 📋 Setup Inicial (Una sola vez)

### 1. Crear Base de Datos (si no existe)

```bash
# Crear BD y usuario
psql -h localhost -U $(whoami) postgres << EOF
CREATE DATABASE guardia;
CREATE USER guardia WITH PASSWORD 'guardia_dev';
ALTER DATABASE guardia OWNER TO guardia;
GRANT ALL PRIVILEGES ON DATABASE guardia TO guardia;
EOF
```

### 2. Correr Migraciones

```bash
cd backend
PYTHONPATH=$PWD .venv/bin/alembic upgrade head
```

### 3. Verificar Configuración de Clerk

Asegúrate de que `backend/.env` tenga configuradas las credenciales de Clerk:

```bash
# backend/.env
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----"
```

---

## 🔥 Levantar Aplicación (2 Terminales)

### Terminal 1: Backend (Python/FastAPI)

```bash
cd backend
PYTHONPATH=$PWD .venv/bin/uvicorn app.main:app --reload --port 8000
```

**Logs en tiempo real:**
- Requests HTTP
- Errores de autenticación
- Pipeline execution
- Queries SQL (solo si `APP_ENV=local` y `APP_DEBUG=true`)

**Endpoints:**
- API: http://localhost:8000/api/v1
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

---

### Terminal 2: Frontend (Vue/Vite)

```bash
cd frontend
npm run dev
```

**Logs en tiempo real:**
- Hot Module Replacement (HMR)
- Warnings de Vue/TypeScript
- Network requests (en DevTools)

**URL:**
- Frontend: http://localhost:3000

---

## 🛑 Detener Aplicación

**Opción 1: Graceful shutdown (RECOMENDADO)**
- En cada terminal: `Ctrl+C`
- Espera a que cierre conexiones de BD

**Opción 2: Force kill**
```bash
# Desde la raíz del proyecto
lsof -ti:8000,3000 | xargs kill
```

⚠️ **IMPORTANTE**: Usar `Ctrl+C` permite que el backend cierre las conexiones de BD correctamente.

---

## 🧪 Ingestar Email de Prueba

Una vez levantado todo:

1. Abre http://localhost:3000
2. Inicia sesión con Google via Clerk
3. Ve a **Monitoring**
4. Click en **"Ingest Email"**
5. Llena el formulario:
   - Sender: `attacker@phishing.com`
   - Recipient: `security@strikesecurity.io`
   - Subject: `Urgent: Password Reset Required`
   - Body: `Click here to reset your password: http://evil.com`
6. Click **"Ingest Email"**

El pipeline procesará el email y verás datos en Dashboard y Monitoring.

---

## 🔍 Activar/Desactivar SQL Logs

**Para ver queries SQL en detalle** (útil para debugging):
```bash
# En backend/.env
APP_ENV=local
APP_DEBUG=true
```

**Para logs limpios** (recomendado para desarrollo normal):
```bash
# En backend/.env
APP_ENV=local
APP_DEBUG=false
```

⚠️ **Importante**: En staging/producción, `APP_ENV` debe ser `staging` o `production`, nunca `local`. Esto desactivará automáticamente los SQL logs sin importar el valor de `APP_DEBUG`.

---

## 🐛 Troubleshooting

### Error: "relation does not exist"
```bash
cd backend
PYTHONPATH=$PWD .venv/bin/alembic upgrade head
```

### Error: "database is being accessed by other users"
```bash
# Terminar conexiones y recrear BD
psql -h localhost -U $(whoami) postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'guardia' AND pid <> pg_backend_pid();"
psql -h localhost -U $(whoami) postgres -c "DROP DATABASE guardia;"
psql -h localhost -U $(whoami) postgres -c "CREATE DATABASE guardia; ALTER DATABASE guardia OWNER TO guardia;"

# Correr migraciones
cd backend
PYTHONPATH=$PWD .venv/bin/alembic upgrade head
```

### Error: "401 Unauthorized"
Verifica que `backend/.env` tenga las credenciales de Clerk configuradas correctamente.

### Error: "CORS policy"
Verifica que `backend/.env` tenga:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend queda en "Loading..."
1. Verifica que el backend esté corriendo (`curl http://localhost:8000/health`)
2. Verifica autenticación en DevTools → Network → Headers
3. Verifica que la BD tenga datos (sino ingesta un email de prueba)

---

## 📊 Logs Útiles

### Ver conexiones activas a PostgreSQL
```bash
psql -h localhost -U $(whoami) guardia -c "SELECT pid, usename, application_name, state FROM pg_stat_activity WHERE datname = 'guardia';"
```

### Ver tablas en BD
```bash
psql -h localhost -U $(whoami) guardia -c "\dt"
```

### Ver últimos casos ingresados
```bash
psql -h localhost -U $(whoami) guardia -c "SELECT case_number, created_at, threat_category, final_score FROM cases ORDER BY created_at DESC LIMIT 5;"
```

---

## 🔄 Recrear BD desde Cero

```bash
# Matar backend
lsof -ti:8000 | xargs kill

# Recrear BD
psql -h localhost -U $(whoami) postgres -c "DROP DATABASE IF EXISTS guardia;"
psql -h localhost -U $(whoami) postgres -c "CREATE DATABASE guardia; ALTER DATABASE guardia OWNER TO guardia;"

# Correr migraciones
cd backend
PYTHONPATH=$PWD .venv/bin/alembic upgrade head

# Levantar backend
PYTHONPATH=$PWD .venv/bin/uvicorn app.main:app --reload --port 8000
```

---

## ✅ Checklist Rápido

Antes de empezar a desarrollar:

- [ ] PostgreSQL corriendo
- [ ] BD `guardia` creada
- [ ] Migraciones ejecutadas
- [ ] `backend/.env` configurado con Clerk
- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 3000
- [ ] Autenticado en http://localhost:3000

---

**Happy Coding! 🚀**
