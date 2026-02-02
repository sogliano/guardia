# Email Ingestion System

Sistema de ingesta realista de emails para Guard-IA con dataset de 50 emails diversos.

## Características

- **50 emails ultra-realistas** con headers RFC 5322 completos (Google Workspace style)
- **Ingesta gradual** (1 email cada ~5 segundos, configurable)
- **API REST** para controlar la ingesta
- **Distribución realista** basada en estadísticas de phishing

## Dataset de 50 Emails

### Distribución por Categoría

| Categoría | Cantidad | % | Descripción |
|-----------|----------|---|-------------|
| **Legítimos** | 17 | 34% | Business emails, newsletters, servicios (GitHub, Slack, AWS, etc.) |
| **Phishing Credenciales** | 12 | 24% | Fake Microsoft, Google, Apple, LinkedIn, PayPal |
| **BEC/Impersonation** | 8 | 16% | CEO fraud, payroll changes, wire transfers |
| **Malware/Attachments** | 6 | 12% | Fake invoices, shipping, IRS refund con .exe |
| **Scams** | 5 | 10% | Crypto, tax, romance, job offer, tech support |
| **Spear Phishing** | 2 | 4% | Targeted HR policies, acquisition announcements |

**Total: 50 emails**

### Ver estadísticas del dataset

```bash
python -c "from scripts.datasets.email_dataset_50 import get_dataset_stats; print(get_dataset_stats())"
```

## API Endpoints

### 1. Iniciar Ingesta

**POST** `/api/v1/ingestion/start`

Inicia ingesta gradual del dataset.

**Headers:**
```
Authorization: Bearer <clerk-jwt-token>
Content-Type: application/json
```

**Body:**
```json
{
  "category": "phishing",  // opcional: legitimate, phishing, bec, malware, scam, spear
  "interval_seconds": 5.0  // tiempo entre emails (default: 5s)
}
```

**Response:**
```json
{
  "message": "Ingestion started",
  "total_emails": 50,
  "interval_seconds": 5.0,
  "category": "all"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 3.0}'
```

### 2. Detener Ingesta

**POST** `/api/v1/ingestion/stop`

Detiene ingesta en curso.

**Response:**
```json
{
  "message": "Ingestion stopped",
  "stats": {
    "total": 50,
    "processed": 23,
    "failed": 0,
    "queue_remaining": 27,
    "started_at": "2026-02-01T10:00:00Z",
    "completed_at": "2026-02-01T10:02:15Z"
  }
}
```

### 3. Ver Estado

**GET** `/api/v1/ingestion/status`

Obtiene estado actual de la cola.

**Response:**
```json
{
  "is_running": true,
  "total": 50,
  "processed": 30,
  "failed": 0,
  "queue_remaining": 20,
  "started_at": "2026-02-01T10:00:00Z",
  "completed_at": null
}
```

### 4. Estadísticas del Dataset

**GET** `/api/v1/ingestion/dataset/stats`

Retorna distribución del dataset.

**Response:**
```json
{
  "total": 50,
  "categories": {
    "legitimate": 17,
    "phishing": 12,
    "bec": 8,
    "malware": 6,
    "scam": 5,
    "spear": 2
  }
}
```

## Ejemplos de Uso

### Ingesta completa (50 emails)

```bash
# Iniciar ingesta de todos los emails
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 5.0}'

# Duración: ~4 minutos (50 emails × 5s)
```

### Ingesta filtrada por categoría

```bash
# Solo emails de phishing (12 emails)
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "phishing", "interval_seconds": 3.0}'

# Duración: ~36 segundos (12 emails × 3s)
```

### Monitoreo en tiempo real

```bash
# Ver progreso cada 2 segundos
watch -n 2 'curl -s http://localhost:8000/api/v1/ingestion/status \
  -H "Authorization: Bearer $JWT_TOKEN" | jq'
```

### Detener ingesta

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/stop \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Logs Estructurados

Durante la ingesta, se generan logs estructurados:

```json
{"event": "dataset_loaded", "count": 50}
{"event": "ingestion_started", "total": 50, "interval": 5.0}
{"event": "email_processed", "email_id": "...", "case_id": "...", "verdict": "quarantined", "score": 0.72, "category": "phishing", "template": "phishing"}
{"event": "email_processed", "email_id": "...", "case_id": "...", "verdict": "allowed", "score": 0.15, "category": "legitimate", "template": "clean"}
...
{"event": "ingestion_completed", "stats": {"total": 50, "processed": 50, "failed": 0}}
```

## Templates Disponibles

### Legítimos (17)
- `clean`, `clean2` - Business emails
- `newsletter`, `newsletter2` - Newsletters (THN, WIRED)
- `github`, `github2` - GitHub notifications
- `calendar` - Google Calendar
- `aws` - AWS billing
- `slack` - Slack notifications
- `jira` - Jira tickets
- `confluence` - Confluence pages
- `linkedin` - LinkedIn connections
- `docusign` - DocuSign documents
- `zoom` - Zoom meetings
- `salesforce` - Salesforce leads
- `stripe` - Stripe receipts
- `hubspot` - HubSpot forms

### Phishing (12)
- `phishing`, `phishing2` - Fake Microsoft/Google
- `apple` - Fake Apple ID
- `gsuite` - Fake Google Workspace admin
- `office365` - Fake Office 365 storage
- `dropbox` - Fake Dropbox share
- `linkedin_phish` - Fake LinkedIn security
- `paypal` - Fake PayPal payment
- `qrphish` - QR code phishing
- `spear` - IT helpdesk fake
- `shareddoc` - Fake Google Docs
- `supply` - Supply chain (fake Slack)

### BEC (8)
- `bec`, `bec2` - CEO impersonation
- `payroll` - Direct deposit fraud
- `cfo` - CFO urgent payment
- `vendor` - Vendor payment change
- `giftcard` - Gift card request
- `legal` - Legal signature request
- `acquisition` - Fake acquisition

### Malware (6)
- `malware` - Fake FedEx
- `invoice`, `invoice2` - Fake invoices
- `irs` - Fake IRS refund
- `ups` - Fake UPS delivery
- `voicemail` - Fake voicemail
- `scanner` - Fake scanner document

### Scams (5)
- `crypto` - Fake Binance
- `tax` - Fake DGI Uruguay
- `romance` - Romance scam
- `joboffer` - Fake job offer
- `techsupport` - Fake Microsoft support

### Spear Phishing (2)
- `hr` - Fake HR policy
- `acquisition` - Fake company announcement

## Testing

### Ejecutar tests del sistema

```bash
# Test completo (templates, dataset, parsing, queue)
python scripts/test_ingestion_system.py
```

### Unit tests (pytest)

```bash
pytest tests/unit/test_ingestion_queue.py -v
```

## Arquitectura

```
POST /api/v1/ingestion/start
  ↓
IngestionQueue.load_dataset(50 emails)
  ↓
Background Task (asyncio) cada 5s:
  ↓
  email = queue.pop()
  ↓
  EmailParser.parse_raw() → dict
  ↓
  Email.create() → persist to DB
  ↓
  Case.create()
  ↓
  PipelineOrchestrator.analyze()
  ↓
  Repeat hasta queue vacía
```

## Headers Realistas (Google Workspace)

Cada email incluye headers ultra-realistas:

```
Authentication-Results: mx.google.com; spf=pass; dkim=pass; dmarc=pass
X-Google-SMTP-Source: AGHT+abc123def456...
X-Received: by 2002:a17:90a:1234 with SMTP id xyz
Return-Path: <sender@example.com>
Received: from mail.example.com (mail.example.com [203.0.113.42])
  by guardia.strike.sh with ESMTPS; Sat, 01 Feb 2026 10:00:00 -0800
User-Agent: Microsoft Outlook 16.0
```

Emails sospechosos tienen:
- `spf=fail`, `dkim=fail`, `dmarc=fail`
- User-Agent sospechosos
- Dominios typosquatted

## Extensiones Futuras

### Parser de .mbox (opcional)

Si tienes archivos .mbox reales:

```python
from scripts.datasets.mbox_parser import load_mbox_dataset

# Cargar emails reales desde .mbox
dataset = load_mbox_dataset("path/to/mailbox.mbox", max_emails=50)

# Usar con ingestion queue
queue = get_queue()
queue.load_dataset(dataset)
await queue.start()
```

### Dashboard Widget (frontend)

Agregar widget en `/monitoring` que consulte `/api/v1/ingestion/status` cada 2s:
- Progress bar (processed / total)
- Emails por segundo
- Tiempo restante estimado
- Botón "Stop Ingestion"

## Troubleshooting

### Ingesta muy lenta

Reducir `interval_seconds`:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -d '{"interval_seconds": 1.0}'  # 1 email por segundo
```

### Pipeline timeout

Si el pipeline tarda >5s por email, aumentar `interval_seconds`:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -d '{"interval_seconds": 10.0}'  # Más tiempo para procesar
```

### Ver logs en tiempo real

```bash
# En el terminal del backend
tail -f logs/guardia.log | grep ingestion
```

## Permisos

- **Iniciar/Detener ingesta:** Solo administradores (`RequireAdmin`)
- **Ver estado:** Cualquier usuario autenticado (`CurrentUser`)
- **Ver estadísticas dataset:** Cualquier usuario autenticado

## Rate Limiting

- `POST /ingestion/start`: 5 req/min
- `POST /ingestion/stop`: 10 req/min
- `GET /ingestion/status`: 60 req/min
- `GET /ingestion/dataset/stats`: 60 req/min
