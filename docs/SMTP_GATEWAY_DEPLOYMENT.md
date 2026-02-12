# SMTP Gateway Deployment Guide

Guia completa para deployar el SMTP Gateway de Guard-IA en una VM de GCP, configurar el modelo ML, DNS y conectar con Google Workspace como Inbound Gateway.

---

## Arquitectura

```
Email sender (cualquier servidor SMTP)
       |
    Puerto 25
       |
[VM GCP: smtp.guardia-sec.com]     <-- aiosmtpd recibe emails
  IP: 34.138.132.198
       |
    Pipeline de deteccion (3 capas)
    1. Heuristics  (~5ms)   - reglas locales
    2. ML/DistilBERT (~18ms) - clasificacion binaria
    3. LLM/OpenAI  (~2-3s)  - explicacion
       |
    Gmail API (primary)                 SMTP Relay (fallback)
    users.messages.import               aspmx.l.google.com
       |                                     |
[Inbox usuario@guardia-sec.com]    [Inbox usuario@guardia-sec.com]

    Internal API (:8025)            <-- Cloud Run llama para quarantine release
```

### Por que una VM y no Cloud Run

Cloud Run solo expone puertos HTTP/HTTPS (8080). SMTP requiere puerto 25, que es un protocolo TCP directo, no HTTP. Por eso el SMTP Gateway corre en una VM de GCE con puerto 25 abierto.

La VM ejecuta todo el pipeline de deteccion localmente: heuristicas, modelo ML (DistilBERT, 66M parametros) y LLM explainer (llamada HTTP a OpenAI). Esto permite que un email sea analizado en ~3-5 segundos end-to-end.

### Componentes que corren en la VM

| Componente | Descripcion | Dependencia |
|------------|-------------|-------------|
| aiosmtpd | Servidor SMTP (puerto 25) | Python stdlib |
| Email Parser | Parseo RFC 5322 | Python stdlib |
| Heuristic Engine | 4 sub-engines (auth, domain, URL, keyword) | Ninguna |
| ML Classifier | DistilBERT fine-tuned, clasificacion binaria + XAI (attention tokens) | PyTorch, Transformers |
| LLM Explainer | Genera explicacion estructurada del analisis | OpenAI API (HTTP) |
| Gmail Delivery | Entrega via Gmail API `users.messages.import` (primary) | google-auth, google-api-python-client |
| Relay Client | Gmail API delivery (primary) + SMTP relay fallback | aiosmtplib (fallback) |
| Internal API | HTTP API :8025 para operaciones de quarantine desde Cloud Run | FastAPI, uvicorn |
| SQLAlchemy async | Persiste emails, cases, analyses, evidences | asyncpg, Neon PostgreSQL |

---

## 1. Infraestructura GCP

### 1.1 Proyecto y APIs

**Proyecto:** `gen-lang-client-0127131422` (GUARD-IA)
**Project Number:** `81580052566`

```bash
# Habilitar Compute Engine API (si no esta habilitada)
gcloud services enable compute.googleapis.com --project=gen-lang-client-0127131422
```

### 1.2 IP Estatica

```bash
# Crear IP estatica
gcloud compute addresses create guardia-smtp-ip \
  --region=us-east1 \
  --network-tier=PREMIUM \
  --project=gen-lang-client-0127131422

# Verificar IP asignada
gcloud compute addresses describe guardia-smtp-ip \
  --region=us-east1 \
  --format='value(address)'
```

**IP asignada:** `34.138.132.198`

### 1.3 VM (e2-small)

> **Importante:** Se requiere minimo **e2-small (2 GB RAM)** para correr PyTorch + DistilBERT.
> Una e2-micro (1 GB) no tiene suficiente memoria: `import torch` se cuelga por falta de RAM
> y el ML stage nunca se ejecuta, cayendo a modo degradado (solo heuristicas + LLM).

```bash
# Crear VM
gcloud compute instances create guardia-smtp-gateway \
  --zone=us-east1-b \
  --machine-type=e2-small \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --address=guardia-smtp-ip \
  --tags=smtp-server \
  --boot-disk-size=20GB \
  --project=gen-lang-client-0127131422
```

**Specs:**
- **Tipo:** e2-small (2 vCPU shared, 2 GB RAM)
- **Costo:** ~$17/mes
- **OS:** Debian 12
- **Disco:** 20 GB
- **Zona:** us-east1-b
- **IP externa:** 34.138.132.198 (estatica)
- **IP interna:** 10.142.0.2

#### Requisitos de memoria

| Componente | RAM aproximada |
|------------|---------------|
| Python + aiosmtpd + SQLAlchemy | ~150 MB |
| PyTorch (CPU) | ~500 MB |
| DistilBERT model (66M params) | ~260 MB |
| OS + sistema | ~300 MB |
| **Total minimo** | **~1.2 GB** |

Con e2-micro (1 GB) el proceso entra en thrashing al intentar cargar PyTorch.
Con e2-small (2 GB) hay margen suficiente para el pipeline completo.

#### Upgrade de e2-micro a e2-small

Si la VM fue creada como e2-micro y necesitas upgradear:

```bash
# Desde tu maquina local (no desde la VM):

# 1. Parar la VM
gcloud compute instances stop guardia-smtp-gateway \
  --zone=us-east1-b \
  --project=gen-lang-client-0127131422

# 2. Cambiar machine type
gcloud compute instances set-machine-type guardia-smtp-gateway \
  --zone=us-east1-b \
  --machine-type=e2-small \
  --project=gen-lang-client-0127131422

# 3. Arrancar la VM
gcloud compute instances start guardia-smtp-gateway \
  --zone=us-east1-b \
  --project=gen-lang-client-0127131422
```

### 1.4 Firewall

```bash
# Permitir SMTP (puerto 25) desde cualquier IP
gcloud compute firewall-rules create allow-smtp \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:25 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=smtp-server \
  --project=gen-lang-client-0127131422
```

La regla aplica solo a VMs con tag `smtp-server`.

---

## 2. Setup de la VM

### 2.1 Conectar por SSH

```bash
gcloud compute ssh guardia-smtp-gateway --zone=us-east1-b --project=gen-lang-client-0127131422
```

### 2.2 Instalar dependencias del sistema

```bash
sudo apt update && sudo apt upgrade -y

# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Build dependencies (para compilar wheels)
sudo apt install -y build-essential libffi-dev libssl-dev
```

### 2.3 Clonar repositorio y setup

```bash
# Clonar repo
git clone https://github.com/sogliano/guardia.git /opt/guardia
cd /opt/guardia/backend

# Crear virtualenv
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -e ".[dev]"
```

### 2.4 Descargar modelo ML (DistilBERT)

El pipeline ML requiere el modelo DistilBERT fine-tuned. Sin el modelo, el pipeline opera en modo degradado (solo heuristicas + LLM), lo cual reduce significativamente la precision de deteccion.

```bash
# Crear directorio del modelo
sudo mkdir -p /opt/guardia/backend/ml_models/distilbert-guardia
sudo chown -R $USER:$USER /opt/guardia/backend/ml_models

# Descargar modelo desde HuggingFace Hub
/opt/guardia/backend/venv/bin/python -c "from huggingface_hub import snapshot_download; path = snapshot_download('Rodrigo-Miranda-0/distilbert-guardia-v2', local_dir='/opt/guardia/backend/ml_models/distilbert-guardia'); print('Model downloaded to:', path)"
```

> Si el repositorio de HuggingFace es privado, agregar el token:
> ```bash
> HF_TOKEN=hf_xxx /opt/guardia/backend/venv/bin/python -c "from huggingface_hub import snapshot_download; path = snapshot_download('Rodrigo-Miranda-0/distilbert-guardia-v2', local_dir='/opt/guardia/backend/ml_models/distilbert-guardia', token='hf_xxx'); print('Downloaded to:', path)"
> ```

#### Verificar que el modelo carga correctamente

```bash
# Verificar torch
/opt/guardia/backend/venv/bin/python -c "import torch; print('torch OK, version:', torch.__version__)"

# Verificar modelo (tarda ~10-15s la primera vez)
/opt/guardia/backend/venv/bin/python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; m = AutoModelForSequenceClassification.from_pretrained('/opt/guardia/backend/ml_models/distilbert-guardia'); t = AutoTokenizer.from_pretrained('/opt/guardia/backend/ml_models/distilbert-guardia'); print('Model loaded OK, params:', sum(p.numel() for p in m.parameters()))"
```

Resultado esperado: `Model loaded OK, params: 66955010`

### 2.5 Configurar variables de entorno

Crear `/opt/guardia/backend/.env`:

```bash
# SMTP Gateway
SMTP_HOST=0.0.0.0
SMTP_PORT=25
SMTP_DOMAIN=smtp.guardia-sec.com
SMTP_TLS_CERT=
SMTP_TLS_KEY=
SMTP_REQUIRE_TLS=false

# Gmail API delivery (primary)
GOOGLE_SERVICE_ACCOUNT_JSON=/opt/guardia/backend/service-account.json
ACCEPTED_DOMAINS=guardia-sec.com

# SMTP Relay fallback (used when Gmail API not configured)
GOOGLE_RELAY_HOST=aspmx.l.google.com
GOOGLE_RELAY_PORT=25

# Database (Neon staging)
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<database>?sslmode=require

# Pipeline
PIPELINE_TIMEOUT_SECONDS=30
THRESHOLD_ALLOW=0.3
THRESHOLD_WARN=0.6
THRESHOLD_QUARANTINE=0.8

# ML Model
ML_MODEL_PATH=./ml_models/distilbert-guardia
ML_MODEL_HF_REPO=Rodrigo-Miranda-0/distilbert-guardia-v2

# OpenAI (LLM explainer)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Quarantine storage
QUARANTINE_STORAGE_PATH=/opt/guardia/quarantine_store

# Internal API (para quarantine release desde Cloud Run)
GATEWAY_INTERNAL_PORT=8025
GATEWAY_INTERNAL_TOKEN=<shared-secret-con-cloud-run>

# Active users (dejar vacio para procesar todos)
ACTIVE_USERS=
```

### 2.6 Crear directorio de quarantine

```bash
sudo mkdir -p /opt/guardia/quarantine_store
sudo chown $USER:$USER /opt/guardia/quarantine_store
```

### 2.7 Probar manualmente

```bash
cd /opt/guardia/backend
source venv/bin/activate
python -m app.gateway.server
```

Deberias ver logs indicando que el SMTP server esta escuchando en puerto 25.
Verificar en los logs que aparezca `ml_model_loaded` -- esto confirma que el modelo DistilBERT cargo correctamente.

### 2.8 Configurar Gmail API Service Account

El gateway usa Gmail API como metodo principal de entrega de emails. Se requiere una service account con domain-wide delegation.

**1. Crear Service Account en GCP Console:**
```bash
gcloud iam service-accounts create guardia-email-delivery \
  --display-name="Guard-IA Email Delivery" \
  --project=gen-lang-client-0127131422
```

**2. Crear JSON key:**
```bash
gcloud iam service-accounts keys create /tmp/service-account.json \
  --iam-account=guardia-email-delivery@gen-lang-client-0127131422.iam.gserviceaccount.com
```

**3. Habilitar Gmail API:**
```bash
gcloud services enable gmail.googleapis.com --project=gen-lang-client-0127131422
```

**4. Configurar Domain-Wide Delegation en Google Admin:**
1. Google Admin Console: https://admin.google.com
2. **Security > API controls > Domain-wide Delegation > Manage**
3. Add new:
   - **Client ID:** (numeric ID de la service account, encontrarlo en IAM > Service Accounts)
   - **OAuth Scopes:** `https://www.googleapis.com/auth/gmail.insert`

**5. Copiar JSON key a la VM:**
```bash
# Desde tu maquina local
gcloud compute scp /tmp/service-account.json guardia-smtp-gateway:/opt/guardia/backend/service-account.json --zone=us-east1-b
```

**6. Verificar:** Despues de reiniciar el servicio, los logs deben mostrar `relay_using_gmail_api` cuando se procesa un email.

### 2.9 Verificar Internal API

Cuando `GATEWAY_INTERNAL_TOKEN` esta configurado, el server tambien levanta un HTTP API en el puerto 8025. Este API es usado por Cloud Run para operaciones de quarantine (release/delete).

```bash
# Health check (no requiere auth)
curl http://localhost:8025/internal/health

# Endpoints disponibles (requieren X-Gateway-Token header):
# POST /internal/quarantine/{case_id}/release  — libera email quarantineado
# POST /internal/quarantine/{case_id}/delete   — elimina .eml del disco
```

---

## 3. Systemd Service (Auto-restart)

Crear `/etc/systemd/system/guardia-smtp.service`:

```ini
[Unit]
Description=Guard-IA SMTP Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/guardia/backend
Environment=PATH=/opt/guardia/backend/venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/guardia/backend/venv/bin/python -m app.gateway.server
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> **Nota:** Se usa `User=root` porque puerto 25 requiere privilegios root. Una alternativa mas segura es usar `setcap` o `authbind` para permitir a un usuario no-root usar puertos bajos.

```bash
# Habilitar y arrancar
sudo systemctl daemon-reload
sudo systemctl enable guardia-smtp
sudo systemctl start guardia-smtp

# Verificar status
sudo systemctl status guardia-smtp

# Ver logs
sudo journalctl -u guardia-smtp -f
```

---

## 4. Configurar DNS (Namecheap)

En Namecheap > Domain List > `guardia-sec.com` > **Advanced DNS**:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | `smtp` | `34.138.132.198` | Automatic |
| MX Record | `@` | `smtp.guardia-sec.com` | Automatic (priority 10) |

**Resultado:**
- `smtp.guardia-sec.com` resuelve a `34.138.132.198`
- Los emails a `*@guardia-sec.com` van primero a `smtp.guardia-sec.com:25`

### Verificar propagacion DNS

```bash
# Verificar A record
dig smtp.guardia-sec.com A +short
# Esperado: 34.138.132.198

# Verificar MX record
dig guardia-sec.com MX +short
# Esperado: 10 smtp.guardia-sec.com.
```

> La propagacion DNS puede tardar entre 5 minutos y 48 horas. Normalmente es < 30 minutos.

---

## 5. Configurar Google Workspace

### 5.1 Crear cuenta Google Workspace
1. Ir a https://workspace.google.com/
2. Crear organizacion con dominio `guardia-sec.com`
3. Verificar dominio (TXT record en Namecheap)

### 5.2 Configurar Gmail MX Records
Para que Gmail pueda recibir emails desde Guard-IA, se necesitan los MX records de Google **ademas** de Guard-IA. Pero los MX records de Google NO se agregan todavia (el MX principal apunta a Guard-IA). Guard-IA forward via SMTP directo a `aspmx.l.google.com`.

### 5.3 Configurar Inbound Gateway
1. Google Admin Console: https://admin.google.com
2. Navegar a: **Apps > Google Workspace > Gmail > Spam, Phishing and Malware**
3. Click en **Inbound gateway**
4. Configurar:
   - **Gateway IPs:** `34.138.132.198`
   - **Automatically detect external IP:** Checked
   - **Reject all mail not from gateway IPs:** Checked
   - **Require TLS for connections from the email gateways listed above:** Checked (recomendado)
5. **Save**

> Cambios pueden tardar hasta 24 horas en propagarse, pero normalmente toman efecto en < 1 hora.

**Que hace esto:**
- Gmail sabe que `34.138.132.198` es tu gateway confiable
- Gmail ignora la IP del gateway al evaluar SPF/spam
- Gmail rechaza emails que no vengan del gateway (evita bypass)

---

## 6. Testing

### 6.1 Test SMTP directo (sin DNS)

Desde tu maquina local, probar conectividad SMTP:

```bash
# Telnet directo a la VM
telnet 34.138.132.198 25

# O con openssl para ver EHLO
openssl s_client -connect 34.138.132.198:25 -starttls smtp
```

### 6.2 Test con swaks (SMTP testing tool)

```bash
# Instalar swaks
brew install swaks  # macOS
# o: sudo apt install swaks  # Debian/Ubuntu

# Enviar email de prueba directo al gateway
swaks \
  --to admin@guardia-sec.com \
  --from test@example.com \
  --server smtp.guardia-sec.com:25 \
  --header "Subject: Test email para Guard-IA" \
  --body "Este es un email de prueba para verificar el SMTP gateway."
```

### 6.3 Test end-to-end (con DNS)

Una vez DNS propagado, enviar email desde cualquier cuenta de Gmail a `admin@guardia-sec.com`.

**Verificar:**
1. Logs de la VM: `sudo journalctl -u guardia-smtp -f`
2. Dashboard Guard-IA: ver caso creado en https://guardia-staging.vercel.app
3. Inbox Google Workspace: email llega a `admin@guardia-sec.com` (si verdict = ALLOW)

### 6.4 Test de quarantine

```bash
# Enviar email con contenido sospechoso
swaks \
  --to admin@guardia-sec.com \
  --from ceo@company-secure-login.com \
  --server smtp.guardia-sec.com:25 \
  --header "Subject: Urgent: Wire Transfer Required Immediately" \
  --body "Please transfer $50,000 to the following account immediately. This is urgent and confidential. Do not verify with anyone else. Account: 123456789, Routing: 987654321."
```

Este email deberia ser detectado como phishing/BEC y quarantineado.

### 6.5 Verificar que el ML stage se ejecuta

Despues de enviar un email de prueba, verificar en los logs que el ML stage se ejecuto:

```bash
sudo journalctl -u guardia-smtp --since "5 minutes ago" --no-pager | grep -i "ml_"
```

Deberias ver:
- `ml_model_loaded` -- modelo cargo correctamente (solo la primera vez)
- `ml_prediction_complete` -- prediccion ejecutada con score y confidence

Si solo ves `ml_model_not_found_locally` o `ml_torch_not_installed`, revisar la seccion 2.4.

---

## 7. Comandos de Administracion

### VM (desde maquina local)

```bash
# SSH a la VM
gcloud compute ssh guardia-smtp-gateway --zone=us-east1-b

# Reiniciar VM
gcloud compute instances reset guardia-smtp-gateway --zone=us-east1-b

# Detener VM (ahorra costos cuando no se usa)
gcloud compute instances stop guardia-smtp-gateway --zone=us-east1-b

# Iniciar VM
gcloud compute instances start guardia-smtp-gateway --zone=us-east1-b

# Ver logs remotamente
gcloud compute ssh guardia-smtp-gateway --zone=us-east1-b --command="sudo journalctl -u guardia-smtp --since '1 hour ago'"
```

### SMTP Service (desde dentro de la VM)

```bash
sudo systemctl status guardia-smtp    # Ver estado
sudo systemctl restart guardia-smtp   # Reiniciar
sudo systemctl stop guardia-smtp      # Parar
sudo journalctl -u guardia-smtp -f    # Logs en vivo
```

### Actualizar codigo en la VM (manual)

```bash
cd /opt/guardia
git pull origin main
sudo systemctl restart guardia-smtp
```

### Actualizacion automatica via GitHub Actions

Los workflows `deploy-backend-staging.yml` y `deploy-backend-production.yml` incluyen un job `sync-smtp-gateway` que automaticamente:

1. Se conecta a la VM via `gcloud compute ssh`
2. Hace `git fetch` + `git checkout` + `git pull` de la branch del deploy
3. Reinstala dependencias con `pip install -e '.[dev]'`
4. Reinicia el servicio `guardia-smtp`

Esto se ejecuta automaticamente despues de cada deploy exitoso al Cloud Run backend, manteniendo la VM sincronizada con la misma version del codigo.

### Actualizar modelo ML

```bash
# Descargar version mas reciente
/opt/guardia/backend/venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('Rodrigo-Miranda-0/distilbert-guardia-v2', local_dir='/opt/guardia/backend/ml_models/distilbert-guardia', force_download=True); print('Done')"

# Reiniciar para cargar el nuevo modelo
sudo systemctl restart guardia-smtp
```

### Eliminar recursos (cleanup)

```bash
# Eliminar VM
gcloud compute instances delete guardia-smtp-gateway --zone=us-east1-b --project=gen-lang-client-0127131422

# Eliminar IP estatica
gcloud compute addresses delete guardia-smtp-ip --region=us-east1 --project=gen-lang-client-0127131422

# Eliminar firewall rule
gcloud compute firewall-rules delete allow-smtp --project=gen-lang-client-0127131422
```

---

## 8. Troubleshooting

### "Connection refused" en puerto 25

1. Verificar que la VM este corriendo: `gcloud compute instances describe guardia-smtp-gateway --zone=us-east1-b --format='value(status)'`
2. Verificar que el servicio este activo: `sudo systemctl status guardia-smtp`
3. Verificar firewall: `gcloud compute firewall-rules describe allow-smtp`
4. Verificar que el proceso escuche en 25: `sudo ss -tlnp | grep :25`

### DNS no resuelve

1. Verificar en Namecheap que los records esten configurados
2. Esperar propagacion (hasta 48h, normalmente < 30min)
3. Probar con `dig smtp.guardia-sec.com A +short`
4. Flush DNS local: `sudo dscacheutil -flushcache` (macOS)

### Emails no llegan a Gmail

1. Verificar logs del gateway: `sudo journalctl -u guardia-smtp -f`
2. Verificar que el relay funcione: el log debe mostrar `email_forwarded` event
3. Verificar que Google Workspace tenga el Inbound Gateway configurado
4. Verificar que el dominio este verificado en Google Admin Console
5. Revisar Google Admin Console > Email Log Search para ver si Gmail rechazo el email

### Pipeline timeout

1. Verificar conectividad a la base de datos desde la VM
2. Verificar que `OPENAI_API_KEY` este configurado
3. Revisar `PIPELINE_TIMEOUT_SECONDS` (default: 30s)

### ML stage no se ejecuta (mode degradado)

Si en los logs ves que el pipeline completa pero sin `ml_prediction_complete`, el ML stage esta en modo degradado. Causas posibles:

1. **RAM insuficiente:** La VM necesita minimo 2 GB. Verificar con `free -m`. Si `available` < 500 MB, upgradear a e2-small (ver seccion 1.3).
2. **torch no instalado o se cuelga al importar:** Ejecutar `/opt/guardia/backend/venv/bin/python -c "import torch; print(torch.__version__)"`. Si se cuelga, es problema de RAM.
3. **Modelo no descargado:** Verificar que exista `/opt/guardia/backend/ml_models/distilbert-guardia/model.safetensors`. Si no existe, seguir seccion 2.4.
4. **Modelo corrupto:** Borrar y re-descargar: `rm -rf /opt/guardia/backend/ml_models/distilbert-guardia && ` seguir seccion 2.4.

**Impacto del modo degradado:** Sin ML, la formula de scoring cambia de `0.30*H + 0.50*ML + 0.20*LLM` a `0.60*H + 0.40*LLM`. Esto produce scores sistematicamente mas bajos porque las heuristicas son conservadoras, resultando en que amenazas obvias queden como WARNED en vez de QUARANTINED/BLOCKED.

### Puerto 25 bloqueado por ISP

Algunos ISPs bloquean el puerto 25 saliente. Si no podes enviar emails de prueba desde tu casa:
- Usar `swaks` desde otra VM en la nube
- Usar el servicio de testing de Google: enviar desde Gmail directo

---

## 9. Costos Estimados

| Recurso | Costo Mensual |
|---------|---------------|
| VM e2-small (2 GB RAM) | ~$17.00 |
| IP estatica (en uso) | $0.00 |
| IP estatica (VM apagada) | ~$7.30 |
| Disco 20GB | ~$1.00 |
| Egress (< 1GB/mes) | $0.00 |
| **Total (VM encendida)** | **~$18.00/mes** |

> **Tip:** Si solo necesitas la VM para testing, podes apagarla cuando no la uses con `gcloud compute instances stop guardia-smtp-gateway --zone=us-east1-b`. La IP estatica se cobra mientras la VM este apagada (~$7.30/mes), asi que si vas a apagar la VM por mucho tiempo, considera liberar la IP.

---

## 10. Resumen de Recursos

| Recurso | Nombre | Detalle |
|---------|--------|---------|
| IP estatica | `guardia-smtp-ip` | 34.138.132.198 (us-east1) |
| VM | `guardia-smtp-gateway` | e2-small, Debian 12, us-east1-b |
| Firewall rule | `allow-smtp` | TCP:25, tag smtp-server |
| DNS A Record | `smtp.guardia-sec.com` | 34.138.132.198 |
| DNS MX Record | `guardia-sec.com` | smtp.guardia-sec.com (priority 10) |
| ML Model | `distilbert-guardia` | /opt/guardia/backend/ml_models/distilbert-guardia (66M params) |
