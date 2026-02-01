# Rotación de Secretos - Guard-IA

**Fecha de creación:** 2026-02-01
**Última actualización:** 2026-02-01

## ⚠️ ACCIÓN REQUERIDA INMEDIATA

Los siguientes secretos están expuestos en archivos `.env` locales y deben ser rotados **antes de hacer deployment a producción**.

---

## 1. CLERK_SECRET_KEY

**Dónde está expuesto:**
- `.env.local`
- `.env.staging`
- `.env.production`
- `backend/.env`

**Cómo rotar:**

1. Login a [Clerk Dashboard](https://dashboard.clerk.com)
2. Navegar a **API Keys** en el proyecto Guard-IA
3. **Revocar** la clave actual que comienza con `sk_test_...`
4. **Generar** una nueva clave
5. **Actualizar** en las siguientes ubicaciones:
   - Railway/Cloud Run environment variables
   - Deployment secrets (NO committear)
   - `.env.local` (solo para desarrollo local)

**Verificar:**
```bash
curl -H "Authorization: Bearer NEW_CLERK_KEY" \
  https://api.clerk.com/v1/users
```

---

## 2. OPENAI_API_KEY

**Dónde está expuesto:**
- `.env.local`
- `.env.staging`
- `.env.production`
- `backend/.env`

**Cómo rotar:**

1. Login a [OpenAI Platform](https://platform.openai.com)
2. Navegar a **API keys**
3. **Revocar** la clave expuesta que comienza con `sk-proj-...`
4. **Crear** una nueva API key
5. **Configurar** límites de uso (rate limits):
   - Max requests: 100/min
   - Max tokens: 100,000/day (ajustar según uso)
6. **Actualizar** en environment variables de producción

**Verificar:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer NEW_OPENAI_KEY"
```

---

## 3. SLACK_WEBHOOK_URL

**Dónde está expuesto:**
- `.env.local`
- `.env.staging`
- `.env.production`

**Cómo rotar:**

1. Login a Slack workspace de Strike Security
2. Navegar a **Apps** → **Incoming Webhooks**
3. **Revocar** el webhook actual (`https://hooks.slack.com/services/...`)
4. **Crear** nuevo webhook apuntando al canal `#guardia-alerts`
5. **Actualizar** en environment variables

**Verificar:**
```bash
curl -X POST NEW_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test rotation OK"}'
```

---

## 4. NEON_DATABASE_URL

**Dónde está expuesto:**
- `.env.local`
- `.env.staging`
- `.env.production`

**Cómo rotar:**

1. Login a [Neon Console](https://console.neon.tech)
2. Seleccionar proyecto **guardia-production**
3. Settings → **Reset password** para usuario `neondb_owner`
4. **Copiar** nuevo password generado
5. **Reconstruir** connection string:
   ```
   postgresql+asyncpg://neondb_owner:NEW_PASSWORD@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **Actualizar** en:
   - Railway: `DATABASE_URL` environment variable
   - Cloud Run: Secret Manager
   - Verificar que backend se reconecta correctamente

**Verificar:**
```bash
psql "postgresql://neondb_owner:NEW_PASSWORD@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  -c "SELECT version();"
```

---

## 5. POSTGRES_PASSWORD (Docker Compose Local)

**Dónde está expuesto:**
- `docker-compose.yml` (ya corregido para usar variable de entorno)

**Cómo configurar:**

1. **NO usar** password hardcodeado en `docker-compose.yml`
2. Configurar en `.env.local`:
   ```bash
   POSTGRES_PASSWORD=guardia_dev_local_CHANGE_ME
   ```
3. Levantar servicios:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

**Nota:** Este password es solo para desarrollo local. Producción usa Neon DB.

---

## Checklist de Rotación

**Antes de deployment a producción:**

- [ ] CLERK_SECRET_KEY rotada en Clerk Dashboard
- [ ] OPENAI_API_KEY rotada en OpenAI Platform
- [ ] SLACK_WEBHOOK_URL regenerada en Slack
- [ ] NEON_DATABASE_URL password reseteado en Neon Console
- [ ] Variables de entorno actualizadas en Railway/Cloud Run
- [ ] Tests de integración ejecutados con nuevas credenciales
- [ ] Verificar que servicios externos responden correctamente
- [ ] Documentar fecha de rotación en este archivo

**Después de rotación:**

- [ ] Eliminar archivos `.env.*` de máquinas locales (si contienen secretos viejos)
- [ ] Cambiar permisos de nuevos archivos `.env.*` a 600:
   ```bash
   chmod 600 .env.local .env.staging .env.production backend/.env
   ```
- [ ] Verificar que `.gitignore` incluye todos los archivos `.env.*`
- [ ] Verificar que historial de git NO contiene secretos:
   ```bash
   git log --all --full-history -- .env.local .env.staging .env.production backend/.env
   ```

---

## Configuración de Variables de Entorno en Producción

### Railway

1. Dashboard → **guardia-backend** → **Variables**
2. Agregar/Actualizar:
   ```
   CLERK_SECRET_KEY=sk_live_NEW_KEY
   OPENAI_API_KEY=sk-proj-NEW_KEY
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/NEW_WEBHOOK
   DATABASE_URL=postgresql+asyncpg://...NEW_PASSWORD...
   CORS_ORIGINS=https://guardia.strike.sh
   RATE_LIMIT_PER_MINUTE=100
   ```
3. Redeploy automáticamente al guardar

### Google Cloud Run

1. Console → **Cloud Run** → **guardia-backend** → **Edit & Deploy New Revision**
2. **Variables & Secrets** → Agregar:
   - `CLERK_SECRET_KEY`: Usar Secret Manager
   - `OPENAI_API_KEY`: Usar Secret Manager
   - `SLACK_WEBHOOK_URL`: Usar Secret Manager
   - `DATABASE_URL`: Usar Secret Manager
3. Deploy nueva revisión

---

## Buenas Prácticas

### ✅ HACER

- Usar variables de entorno para TODOS los secretos
- Rotar secretos cada 90 días (calendario)
- Usar Secret Manager en producción (Railway, GCP Secret Manager)
- Configurar alerts de uso anómalo en OpenAI/Clerk
- Mantener `.env.example` actualizado (sin valores reales)
- Usar permisos 600 para archivos `.env.*`

### ❌ NO HACER

- **NUNCA** committear archivos `.env.*` a git
- **NUNCA** compartir secretos por Slack/Email/WhatsApp
- **NUNCA** hardcodear secretos en código
- **NUNCA** usar mismos secretos en staging y producción
- **NUNCA** hacer `git add .env*` (verificar antes de commit)

---

## Contacto de Emergencia

**Si se detecta exposición de secretos:**

1. **Inmediatamente** revocar credenciales en los servicios afectados
2. Notificar a equipo de seguridad: security@strike.sh
3. Revisar logs de acceso en Clerk/OpenAI/Neon para detectar uso no autorizado
4. Seguir este documento para rotar todos los secretos
5. Investigar cómo ocurrió la exposición y prevenir recurrencia

---

**Última rotación:** [PENDIENTE - Ejecutar antes de producción]
**Próxima rotación programada:** [90 días después de primera rotación]
