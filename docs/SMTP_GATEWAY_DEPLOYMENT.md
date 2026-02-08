# SMTP Gateway Deployment Guide

Guía completa para deployar el SMTP Gateway de Guard-IA en una VM de GCP, configurar DNS y conectar con Google Workspace como Inbound Gateway.

---

## Arquitectura

```
Email sender (cualquier servidor SMTP)
       |
    Puerto 25
       |
[VM GCP: smtp.guardia-sec.com]     ← aiosmtpd recibe emails
  IP: 34.138.132.198
       |
    Análisis (pipeline)
       |
    Forward SMTP
       |
[Gmail: aspmx.l.google.com]        ← Google Workspace recibe emails permitidos
       |
[Inbox usuario@guardia-sec.com]
```

**Por qué una VM y no Cloud Run:**
Cloud Run solo expone puerto 8080 (HTTP/HTTPS). SMTP requiere puerto 25, que es un protocolo TCP directo, no HTTP. Por eso el SMTP Gateway corre en una VM con puerto 25 abierto.

---

## 1. Infraestructura GCP

### 1.1 Proyecto y APIs

**Proyecto:** `gen-lang-client-0127131422` (GUARD-IA)
**Project Number:** `81580052566`

```bash
# Habilitar Compute Engine API (si no está habilitada)
gcloud services enable compute.googleapis.com --project=gen-lang-client-0127131422
```

### 1.2 IP Estática

```bash
# Crear IP estática
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

### 1.3 VM (e2-micro)

```bash
# Crear VM
gcloud compute instances create guardia-smtp-gateway \
  --zone=us-east1-b \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --address=guardia-smtp-ip \
  --tags=smtp-server \
  --boot-disk-size=20GB \
  --project=gen-lang-client-0127131422
```

**Specs:**
- **Tipo:** e2-micro (2 vCPU shared, 1 GB RAM)
- **Costo:** ~$7/mes
- **OS:** Debian 12
- **Disco:** 20 GB
- **Zona:** us-east1-b
- **IP externa:** 34.138.132.198 (estática)
- **IP interna:** 10.142.0.2

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

### 2.4 Configurar variables de entorno

Crear `/opt/guardia/backend/.env`:

```bash
# SMTP Gateway
SMTP_HOST=0.0.0.0
SMTP_PORT=25
SMTP_DOMAIN=smtp.guardia-sec.com
SMTP_TLS_CERT=
SMTP_TLS_KEY=
SMTP_REQUIRE_TLS=false

# Google Workspace Relay
GOOGLE_RELAY_HOST=aspmx.l.google.com
GOOGLE_RELAY_PORT=25
ACCEPTED_DOMAINS=guardia-sec.com

# Database (Neon staging)
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<database>?sslmode=require

# Pipeline
PIPELINE_TIMEOUT_SECONDS=30
THRESHOLD_ALLOW=0.3
THRESHOLD_WARN=0.6
THRESHOLD_QUARANTINE=0.8

# OpenAI (LLM explainer)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1

# Quarantine storage
QUARANTINE_STORAGE_PATH=/opt/guardia/quarantine_store

# Active users (dejar vacío para procesar todos)
ACTIVE_USERS=
```

### 2.5 Crear directorio de quarantine

```bash
sudo mkdir -p /opt/guardia/quarantine_store
sudo chown $USER:$USER /opt/guardia/quarantine_store
```

### 2.6 Probar manualmente

```bash
cd /opt/guardia/backend
source venv/bin/activate
python -m app.gateway.server
```

Deberías ver logs indicando que el SMTP server está escuchando en puerto 25.

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

> **Nota:** Se usa `User=root` porque puerto 25 requiere privilegios root. Una alternativa más segura es usar `setcap` o `authbind` para permitir a un usuario no-root usar puertos bajos.

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

### Verificar propagación DNS

```bash
# Verificar A record
dig smtp.guardia-sec.com A +short
# Esperado: 34.138.132.198

# Verificar MX record
dig guardia-sec.com MX +short
# Esperado: 10 smtp.guardia-sec.com.
```

> La propagación DNS puede tardar entre 5 minutos y 48 horas. Normalmente es < 30 minutos.

---

## 5. Configurar Google Workspace

### 5.1 Crear cuenta Google Workspace
1. Ir a https://workspace.google.com/
2. Crear organización con dominio `guardia-sec.com`
3. Verificar dominio (TXT record en Namecheap)

### 5.2 Configurar Gmail MX Records
Para que Gmail pueda recibir emails desde Guard-IA, se necesitan los MX records de Google **además** de Guard-IA. Pero los MX records de Google NO se agregan todavía (el MX principal apunta a Guard-IA). Guard-IA forwarded via SMTP directo a `aspmx.l.google.com`.

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

**Qué hace esto:**
- Gmail sabe que `34.138.132.198` es tu gateway confiable
- Gmail ignora la IP del gateway al evaluar SPF/spam
- Gmail rechaza emails que no vengan del gateway (evita bypass)

---

## 6. Testing

### 6.1 Test SMTP directo (sin DNS)

Desde tu máquina local, probar conectividad SMTP:

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
  --server 34.138.132.198:25 \
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
  --server 34.138.132.198:25 \
  --header "Subject: Urgent: Wire Transfer Required Immediately" \
  --body "Please transfer $50,000 to the following account immediately. This is urgent and confidential. Do not verify with anyone else. Account: 123456789, Routing: 987654321."
```

Este email debería ser detectado como phishing/BEC y quarantineado.

---

## 7. Comandos de Administración

### VM

```bash
# SSH a la VM
gcloud compute ssh guardia-smtp-gateway --zone=us-east1-b

# Reiniciar VM
gcloud compute instances reset guardia-smtp-gateway --zone=us-east1-b

# Detener VM (ahorra costos cuando no se usa)
gcloud compute instances stop guardia-smtp-gateway --zone=us-east1-b

# Iniciar VM
gcloud compute instances start guardia-smtp-gateway --zone=us-east1-b

# Ver logs
gcloud compute ssh guardia-smtp-gateway --zone=us-east1-b --command="sudo journalctl -u guardia-smtp --since '1 hour ago'"
```

### SMTP Service

```bash
# Dentro de la VM:
sudo systemctl status guardia-smtp    # Ver estado
sudo systemctl restart guardia-smtp   # Reiniciar
sudo systemctl stop guardia-smtp      # Parar
sudo journalctl -u guardia-smtp -f    # Logs en vivo
```

### Eliminar recursos (cleanup)

```bash
# Eliminar VM
gcloud compute instances delete guardia-smtp-gateway --zone=us-east1-b --project=gen-lang-client-0127131422

# Eliminar IP estática
gcloud compute addresses delete guardia-smtp-ip --region=us-east1 --project=gen-lang-client-0127131422

# Eliminar firewall rule
gcloud compute firewall-rules delete allow-smtp --project=gen-lang-client-0127131422
```

---

## 8. Troubleshooting

### "Connection refused" en puerto 25

1. Verificar que la VM esté corriendo: `gcloud compute instances describe guardia-smtp-gateway --zone=us-east1-b --format='value(status)'`
2. Verificar que el servicio esté activo: `sudo systemctl status guardia-smtp`
3. Verificar firewall: `gcloud compute firewall-rules describe allow-smtp`
4. Verificar que el proceso escuche en 25: `sudo ss -tlnp | grep :25`

### DNS no resuelve

1. Verificar en Namecheap que los records estén configurados
2. Esperar propagación (hasta 48h, normalmente < 30min)
3. Probar con `dig smtp.guardia-sec.com A +short`
4. Flush DNS local: `sudo dscacheutil -flushcache` (macOS)

### Emails no llegan a Gmail

1. Verificar logs del gateway: `sudo journalctl -u guardia-smtp -f`
2. Verificar que el relay funcione: el log debe mostrar `email_forwarded` event
3. Verificar que Google Workspace tenga el Inbound Gateway configurado
4. Verificar que el dominio esté verificado en Google Admin Console
5. Revisar Google Admin Console > Email Log Search para ver si Gmail rechazó el email

### Pipeline timeout

1. Verificar conectividad a la base de datos desde la VM
2. Verificar que `OPENAI_API_KEY` esté configurado
3. Revisar `PIPELINE_TIMEOUT_SECONDS` (default: 30s)

### Puerto 25 bloqueado por ISP

Algunos ISPs bloquean el puerto 25 saliente. Si no podés enviar emails de prueba desde tu casa:
- Usar `swaks` desde otra VM en la nube
- Usar el servicio de testing de Google: enviar desde Gmail directo

---

## 9. Costos Estimados

| Recurso | Costo Mensual |
|---------|---------------|
| VM e2-micro | ~$7.00 |
| IP estática (en uso) | $0.00 |
| IP estática (VM apagada) | ~$7.30 |
| Disco 20GB | ~$1.00 |
| Egress (< 1GB/mes) | $0.00 |
| **Total (VM encendida)** | **~$8.00/mes** |

> **Tip:** Si solo necesitás la VM para testing, podés apagarla cuando no la uses con `gcloud compute instances stop guardia-smtp-gateway --zone=us-east1-b`. La IP estática se cobra mientras la VM esté apagada (~$7.30/mes), así que si vas a apagar la VM por mucho tiempo, considerá liberar la IP.

---

## 10. Resumen de Recursos Creados

| Recurso | Nombre | Detalle |
|---------|--------|---------|
| IP estática | `guardia-smtp-ip` | 34.138.132.198 (us-east1) |
| VM | `guardia-smtp-gateway` | e2-micro, Debian 12, us-east1-b |
| Firewall rule | `allow-smtp` | TCP:25, tag smtp-server |
| DNS A Record | `smtp.guardia-sec.com` | 34.138.132.198 |
| DNS MX Record | `guardia-sec.com` | smtp.guardia-sec.com (priority 10) |
