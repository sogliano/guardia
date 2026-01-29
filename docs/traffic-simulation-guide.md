# Guard-IA — Guía de Simulación de Tráfico

Cómo generar tráfico de email realista a través del pipeline de Guard-IA para desarrollo, testing y demos.

---

## Cómo funciona en producción

Cuando Guard-IA está configurado como gateway de entrada en Google Workspace:

```
Internet → MX DNS (strike.sh) → Guard-IA SMTP (:2525) → Pipeline → Gmail
```

1. Google Workspace redirecciona todo el correo entrante a Guard-IA (inbound gateway)
2. Guard-IA recibe el email vía SMTP (protocolo estándar de correo)
3. El parser extrae: sender, subject, body, URLs, attachments, SPF/DKIM/DMARC
4. El pipeline analiza el email en 3 capas secuenciales:
   - **Heurísticas** (~5ms): dominio, URLs, keywords, autenticación
   - **ML/DistilBERT** (~18ms): clasificación binaria legítimo/phishing
   - **LLM** (~2-3s): explicación humana (no decide, solo explica)
5. Guard-IA toma una decisión SMTP:
   - `ALLOWED` (score < 0.3): reenvía a Gmail normalmente
   - `WARNED` (0.3 – 0.6): reenvía a Gmail con headers de advertencia
   - `QUARANTINED` (0.6 – 0.8): almacena localmente, no entrega
   - `BLOCKED` (>= 0.8): rechaza el email (550 SMTP rejection)

### En desarrollo local

```
Script Python → smtplib → Guard-IA SMTP (:2525) → Pipeline → (relay falla silenciosamente)
```

El pipeline completo funciona igual. La única diferencia es que el relay a Google (`aspmx.l.google.com:25`) falla porque no hay DNS real. Los emails se procesan, se crean Cases, Analyses y Evidences — y son visibles en el frontend.

---

## Prerequisitos

```bash
# Terminal 1: Levantar toda la infraestructura
make dev

# Esto inicia:
#   PostgreSQL en :5432
#   Backend API en :8000
#   SMTP Gateway en :2525
#   Frontend en :3000
```

Verificar que el gateway SMTP esté escuchando:

```bash
# Test rápido de conexión SMTP
python3 -c "
import smtplib
with smtplib.SMTP('127.0.0.1', 2525, timeout=5) as s:
    s.ehlo('test')
    print('SMTP Gateway OK')
"
```

---

## Método 1: Simulador Built-in (el más rápido)

Guard-IA incluye un simulador con 6 templates realistas que cubren los escenarios principales.

### Enviar todos los templates

```bash
cd backend
python -m scripts.simulate_email --all
```

Esto envía 6 emails a través del pipeline completo. En ~10 segundos tendrás datos en el frontend.

### Enviar un template específico

```bash
python -m scripts.simulate_email --template phishing
python -m scripts.simulate_email --template bec
python -m scripts.simulate_email --template clean
python -m scripts.simulate_email --template malware
python -m scripts.simulate_email --template spear
python -m scripts.simulate_email --template newsletter
```

### Listar templates disponibles

```bash
python -m scripts.simulate_email --list
```

### Load test (múltiples copias)

```bash
# 10 copias del template phishing con 2 segundos entre cada una
python -m scripts.simulate_email --template phishing --count 10 --delay 2

# Destinatario custom
python -m scripts.simulate_email --template bec --to ciso@strike.sh
```

### Templates disponibles

| Template     | Riesgo esperado | Veredicto esperado     | Qué simula                                   |
|--------------|-----------------|------------------------|----------------------------------------------|
| `clean`      | Low             | ALLOWED                | Email legítimo de negocios (Q4 review)        |
| `phishing`   | High/Critical   | QUARANTINED / BLOCKED  | Credential phishing — fake Microsoft login    |
| `bec`        | High/Critical   | QUARANTINED / BLOCKED  | BEC — CEO impersonation, wire transfer        |
| `malware`    | High/Critical   | QUARANTINED / BLOCKED  | Malware — fake FedEx, attachment .pdf.exe     |
| `spear`      | Medium/High     | WARNED / QUARANTINED   | Spear phishing — fake IT helpdesk             |
| `newsletter` | Low             | ALLOWED                | Newsletter legítimo (Hacker News)             |

### Qué señales detecta cada template

**`phishing` — Credential Phishing**
- Sender: `security-alert@m1cr0s0ft-verify.com` (typosquat de "microsoft")
- Subject: `[URGENT] Unusual sign-in activity...`
- URLs: `m1cr0s0ft-verify.com/login/verify`, `bit.ly/3xFakeLink` (URL shortener)
- Auth: SPF=fail, DKIM=fail, DMARC=fail
- Keywords: "urgent", "verify", "account suspended", "immediately"
- → Heurísticas detecta: `DOMAIN_TYPOSQUATTING`, `AUTH_SPF_FAIL`, `AUTH_DKIM_FAIL`, `AUTH_DMARC_FAIL`, `URL_SHORTENER`, `KEYWORD_URGENCY`, `KEYWORD_PHISHING`

**`bec` — CEO Impersonation**
- Sender: `martin.garcia@strikesecurlty.com` (typosquat: "i" → "l")
- Reply-To: `martin.garcia.private@gmail.com` (diferente dominio)
- Subject: `Urgent wire transfer needed — confidential`
- Keywords: "urgent", "wire transfer", "confidential", "$47,500", "Cayman Islands"
- Auth: SPF=softfail, DKIM=fail, DMARC=fail
- → Heurísticas detecta: `DOMAIN_TYPOSQUATTING`, `AUTH_REPLY_TO_MISMATCH`, `AUTH_SPF_FAIL`, `AUTH_DKIM_FAIL`, `KEYWORD_URGENCY`, `KEYWORD_PHISHING`

**`malware` — Fake FedEx**
- Sender: `shipping@fedex-tracking-update.com`
- Attachment: `shipping_label_update.pdf.exe` (doble extensión)
- URL: `fedex-tracking-update.com/label/download`
- Auth: SPF=fail, DKIM=none, DMARC=fail
- → Heurísticas detecta: `DOMAIN_SUSPICIOUS_TLD`, `AUTH_SPF_FAIL`, `AUTH_DMARC_FAIL`, `URL_SUSPICIOUS`

**`spear` — Fake IT Helpdesk**
- Sender: `helpdesk@strikesecurity-it.com` (lookalike domain)
- Subject: `Password expiration notice — Reset required today`
- URL: `strikesecurity-it.com/reset-password`
- Auth: SPF=softfail, DKIM=none, DMARC=none
- → Heurísticas detecta: `DOMAIN_SUSPICIOUS_TLD`, `AUTH_SPF_FAIL`, `KEYWORD_URGENCY`, `KEYWORD_PHISHING`

**`clean` y `newsletter`** — Auth pass, sin señales sospechosas → score bajo, ALLOWED.

---

## Método 2: Generar tráfico mixto a escala

Para popular el dashboard y tener datos representativos:

```bash
cd backend

# Escenario realista: 120 emails (20 rondas × 6 templates)
for i in $(seq 1 20); do
  python -m scripts.simulate_email --all --delay 0.3
done

# O mezcla manual con proporciones realistas:
# ~70% legítimos, ~15% medium risk, ~15% high risk
python -m scripts.simulate_email --template clean --count 35 --delay 0.2
python -m scripts.simulate_email --template newsletter --count 35 --delay 0.2
python -m scripts.simulate_email --template spear --count 15 --delay 0.2
python -m scripts.simulate_email --template phishing --count 5 --delay 0.2
python -m scripts.simulate_email --template bec --count 5 --delay 0.2
python -m scripts.simulate_email --template malware --count 5 --delay 0.2
```

---

## Método 3: Emails reales desde Gmail (MBOX Export)

El enfoque más realista — inyectar tus emails reales al pipeline.

### Paso 1: Exportar desde Google Takeout

1. Ir a [https://takeout.google.com](https://takeout.google.com)
2. Deseleccionar todo, marcar solo **Mail**
3. Click "All Mail data included" → seleccionar labels o "All Mail"
4. Formato: **MBOX**
5. Método: "Download link via email"
6. Crear exportación y esperar (minutos a horas según volumen)
7. Descargar el archivo `.mbox`

### Paso 2: Replay del MBOX

```python
#!/usr/bin/env python3
"""Replay de archivo MBOX a través del SMTP gateway de Guard-IA."""

import mailbox
import smtplib
import sys
import time


def replay_mbox(
    mbox_path: str,
    host: str = "127.0.0.1",
    port: int = 2525,
    recipient: str = "analyst@strike.sh",
    delay: float = 1.0,
    limit: int = 0,
):
    """Enviar emails de un archivo MBOX al gateway SMTP de Guard-IA."""
    mbox = mailbox.mbox(mbox_path)
    total = len(mbox)
    print(f"Found {total} emails in {mbox_path}")

    sent = 0
    errors = 0

    for i, message in enumerate(mbox):
        if limit > 0 and sent >= limit:
            break

        sender = message.get("From", "unknown@unknown.com")
        subject = message.get("Subject", "(no subject)")
        print(f"[{i+1}/{total}] From: {sender[:50]} | Subject: {subject[:60]}")

        try:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.ehlo("mbox-replay.guardia.local")
                smtp.sendmail(
                    from_addr=sender,
                    to_addrs=[recipient],
                    msg=message.as_bytes(),
                )
            sent += 1
            print("  -> Sent OK")
        except smtplib.SMTPResponseException as e:
            print(f"  -> SMTP {e.smtp_code}: {e.smtp_error}")
            sent += 1  # Gateway lo procesó, aunque lo haya rechazado/quarantined
        except Exception as e:
            print(f"  -> ERROR: {e}")
            errors += 1

        time.sleep(delay)

    print(f"\nDone: {sent} sent, {errors} errors out of {total}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python replay_mbox.py <path-to-mbox-file> [limit]")
        sys.exit(1)

    mbox_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    replay_mbox(mbox_path, limit=limit)
```

```bash
# Todos los emails
python replay_mbox.py ~/Downloads/All\ Mail.mbox

# Solo los primeros 50
python replay_mbox.py ~/Downloads/All\ Mail.mbox 50
```

---

## Método 4: Gmail IMAP (selectivo, en vivo)

Conectar a Gmail vía IMAP, descargar emails recientes y reenviarlos a Guard-IA.

### Setup

1. Habilitar IMAP en Gmail: Settings → "Forwarding and POP/IMAP" → Enable IMAP
2. Crear App Password en [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requiere 2FA)

### Script

```python
#!/usr/bin/env python3
"""Fetch emails from Gmail IMAP and replay through Guard-IA."""

import email
import imaplib
import smtplib
import time

# ── Config ──
GMAIL_USER = "tu.email@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # App Password, NO tu password normal

GUARDIA_HOST = "127.0.0.1"
GUARDIA_PORT = 2525
RECIPIENT = "analyst@strike.sh"


def fetch_and_replay(folder: str = "INBOX", limit: int = 20, delay: float = 1.0):
    """Fetch emails from Gmail and send to Guard-IA."""
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    imap.select(folder, readonly=True)

    status, msg_ids = imap.search(None, "(SINCE 01-Jan-2025)")
    if status != "OK":
        print("IMAP search failed")
        return

    ids = msg_ids[0].split()
    print(f"Found {len(ids)} emails in {folder}")
    ids = ids[-limit:]  # Últimos N emails

    sent = 0
    for uid in ids:
        status, data = imap.fetch(uid, "(RFC822)")
        if status != "OK":
            continue

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        sender = msg.get("From", "unknown")
        subject = msg.get("Subject", "(no subject)")

        print(f"  From: {sender[:50]} | Subject: {subject[:60]}")

        try:
            with smtplib.SMTP(GUARDIA_HOST, GUARDIA_PORT, timeout=30) as smtp:
                smtp.ehlo("imap-replay.guardia.local")
                smtp.sendmail(
                    from_addr=sender,
                    to_addrs=[RECIPIENT],
                    msg=raw_email,
                )
            sent += 1
        except Exception as e:
            print(f"    ERROR: {e}")

        time.sleep(delay)

    imap.logout()
    print(f"\nDone: {sent} sent out of {len(ids)}")


if __name__ == "__main__":
    fetch_and_replay(folder="INBOX", limit=30)
```

```bash
# Editar las credenciales en el script, luego:
python imap_replay.py
```

---

## Método 5: Gmail API (OAuth2, más robusto)

Usa la API oficial de Gmail con OAuth2.

### Setup

1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Crear proyecto → Habilitar Gmail API
3. Crear credenciales OAuth 2.0 (Desktop app)
4. Descargar `credentials.json`

```bash
pip install google-auth-oauthlib google-api-python-client
```

### Script

```python
#!/usr/bin/env python3
"""Gmail API → Guard-IA replay."""

import base64
import os
import smtplib
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GUARDIA_HOST = "127.0.0.1"
GUARDIA_PORT = 2525
RECIPIENT = "analyst@strike.sh"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def replay_gmail(limit: int = 30, query: str = "newer_than:7d", delay: float = 1.0):
    """Fetch emails via Gmail API and send to Guard-IA."""
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me", q=query, maxResults=limit
    ).execute()

    messages = results.get("messages", [])
    print(f"Found {len(messages)} emails matching query: {query}")

    sent = 0
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="raw"
        ).execute()

        raw_bytes = base64.urlsafe_b64decode(msg["raw"])
        snippet = msg.get("snippet", "")[:60]
        print(f"  [{sent+1}] {snippet}...")

        try:
            with smtplib.SMTP(GUARDIA_HOST, GUARDIA_PORT, timeout=30) as smtp:
                smtp.ehlo("gmail-api-replay.guardia.local")
                smtp.sendmail(
                    from_addr="replay@guardia.local",
                    to_addrs=[RECIPIENT],
                    msg=raw_bytes,
                )
            sent += 1
        except Exception as e:
            print(f"    ERROR: {e}")

        time.sleep(delay)

    print(f"\nDone: {sent} sent out of {len(messages)}")


if __name__ == "__main__":
    replay_gmail(limit=50, query="newer_than:30d")
```

---

## Método 6: Importar archivos .eml

Si tenés archivos `.eml` (exportados de Thunderbird, Outlook, o muestras forenses):

```python
#!/usr/bin/env python3
"""Send .eml files to Guard-IA SMTP gateway."""

import glob
import smtplib
import sys
import time


def send_eml(
    eml_path: str,
    host: str = "127.0.0.1",
    port: int = 2525,
    recipient: str = "analyst@strike.sh",
):
    """Send a single .eml file to Guard-IA."""
    with open(eml_path, "rb") as f:
        raw = f.read()

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo("eml-import.guardia.local")
            smtp.sendmail("import@guardia.local", [recipient], raw)
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*.eml"
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} .eml files")

    for f in files:
        print(f"  Sending {f}...")
        send_eml(f)
        time.sleep(0.5)
```

```bash
python send_eml.py "/path/to/eml-files/*.eml"
```

---

## Quick Start recomendado

### Para probar que funciona (2 minutos)

```bash
cd backend
python -m scripts.simulate_email --all
```

Abrí `http://localhost:3000` → Dashboard, Cases, Quarantine y Email Explorer deberían mostrar datos.

### Para demo representativa (5 minutos)

```bash
cd backend

# 100 emails con distribución realista
python -m scripts.simulate_email --template clean --count 35 --delay 0.2
python -m scripts.simulate_email --template newsletter --count 35 --delay 0.2
python -m scripts.simulate_email --template spear --count 15 --delay 0.2
python -m scripts.simulate_email --template phishing --count 5 --delay 0.2
python -m scripts.simulate_email --template bec --count 5 --delay 0.2
python -m scripts.simulate_email --template malware --count 5 --delay 0.2
```

### Para testing realista con emails propios (30 minutos)

1. Exportar Gmail vía Google Takeout (MBOX)
2. `python replay_mbox.py ~/Downloads/All\ Mail.mbox 50`
3. Mezclar con amenazas simuladas: `python -m scripts.simulate_email --template phishing --count 5`

---

## Flujo de datos completo

```
┌─────────────────────────────────────────────────────────────┐
│  Email (SMTP o Script)                                       │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  SMTP Gateway (:2525) — GuardIAHandler                       │
│  1. EmailParser.parse_raw() → datos estructurados            │
│  2. Persist Email record en PostgreSQL                       │
│  3. Trigger PipelineOrchestrator.analyze()                   │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Orchestrator                                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Heurísticas (~5ms)                            │  │
│  │ ├─ Domain Analysis (25%)   → typosquat, blacklist      │  │
│  │ ├─ URL Analysis (25%)      → shorteners, IPs, TLDs    │  │
│  │ ├─ Keyword Analysis (25%)  → urgency, phishing, BEC   │  │
│  │ └─ Auth Analysis (25%)     → SPF, DKIM, DMARC         │  │
│  │ → Genera Evidence records por cada señal               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Layer 2: ML Classifier (~18ms)                         │  │
│  │ └─ DistilBERT (66M params, max 256 tokens)             │  │
│  │ → Score 0.0-1.0 + Confidence                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Final Score = 40% Heurísticas + 60% ML                     │
│                                                              │
│  Veredicto:                                                  │
│  ├─ < 0.3  → ALLOWED (low risk)                             │
│  ├─ 0.3–0.6 → WARNED (medium risk)                          │
│  ├─ 0.6–0.8 → QUARANTINED (high risk)                       │
│  └─ ≥ 0.8  → BLOCKED (critical risk)                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Layer 3: LLM Explainer (~2-3s) [no-blocking]          │  │
│  │ ├─ Primary: Claude Opus 4.5                            │  │
│  │ └─ Fallback: GPT-4.1                                   │  │
│  │ → Explicación humana (NO decide, solo explica)         │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Decisión SMTP                                               │
│  ├─ ALLOWED/WARNED → Relay a Gmail (aspmx.l.google.com:25) │
│  ├─ QUARANTINED → Store .eml local, no entrega              │
│  └─ BLOCKED → 550 SMTP rejection                            │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Base de datos (PostgreSQL)                                  │
│  Email → Case → Analysis (×3) → Evidence (×N)               │
│  └─ Visible en frontend: Dashboard, Cases, Quarantine       │
└─────────────────────────────────────────────────────────────┘
```

---

## Datos generados por el pipeline

Cada email procesado crea los siguientes registros:

| Tabla       | Cantidad | Descripción                                          |
|-------------|----------|------------------------------------------------------|
| `emails`    | 1        | Email original (sender, subject, body, URLs, auth)   |
| `cases`     | 1        | Container: score, risk_level, verdict, status        |
| `analyses`  | 2-3      | Una por etapa: heuristic, ml, llm                    |
| `evidences` | 0-N      | Una por señal detectada (domain, URL, keyword, auth) |

### Dónde ver los resultados en el frontend

| Sección           | URL                         | Qué muestra                                      |
|-------------------|-----------------------------|--------------------------------------------------|
| **Dashboard**     | `http://localhost:3000/`     | KPIs, gráficos de tendencias, distribución       |
| **Cases**         | `http://localhost:3000/cases`| Tabla de todos los casos con filtros              |
| **Case Detail**   | `http://localhost:3000/cases/:id` | Detalle completo: 3 análisis + evidencias   |
| **Quarantine**    | `http://localhost:3000/quarantine` | Emails retenidos, acciones release/keep/delete |
| **Email Explorer**| `http://localhost:3000/emails`| Todos los emails ingestados                      |

---

## Notas importantes

- **Dominio aceptado**: El gateway SMTP solo acepta emails dirigidos a dominios en `ACCEPTED_DOMAINS` (default: `strike.sh`). Usar `--to analyst@strike.sh` o editar `ACCEPTED_DOMAINS` en `.env`.
- **Relay deshabilitado en local**: El relay a Gmail falla silenciosamente. Los emails se procesan igual — solo no se reenvían.
- **Costo LLM**: Cada email que llega a la etapa LLM cuesta ~$0.01-0.05 (API Claude/GPT). 100 emails ≈ $1-5. Para bulk testing, considerar deshabilitar temporalmente el LLM.
- **Message-ID único**: El pipeline deduplica por `message_id`. Si enviás el mismo template dos veces sin delay, el segundo puede ser ignorado. El simulador genera un `Message-ID` único por cada envío.
- **Reset de datos**: Para limpiar todo y empezar de cero:
  ```bash
  # Truncar tablas (mantiene schema)
  psql -U guardia -d guardia -c "
    TRUNCATE evidences, analyses, cases, emails CASCADE;
  "
  ```
- **Sin modelo ML**: Si el modelo DistilBERT no está disponible (`./ml_models/distilbert-guardia`), el pipeline continúa solo con heurísticas (100% heuristic score). No falla.
