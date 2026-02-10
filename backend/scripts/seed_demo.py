"""
Seed script for Guard-IA demo: ~65 realistic emails over 7 days.

Creates emails with correct model fields, realistic auth_results, and
varied threat categories. Optionally runs the full 3-layer pipeline.

Usage:
    # Full seed with pipeline (staging)
    DATABASE_URL="..." python -m scripts.seed_demo

    # Seed without pipeline
    python -m scripts.seed_demo --no-pipeline

    # Clean existing data first
    python -m scripts.seed_demo --clean

    # Both flags
    DATABASE_URL="..." python -m scripts.seed_demo --clean --no-pipeline
"""

import argparse
import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, text

from app.db.session import async_session_factory
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.email import Email
from app.models.evidence import Evidence
from app.services.pipeline.orchestrator import PipelineOrchestrator

# ---------------------------------------------------------------------------
# Timezone
# ---------------------------------------------------------------------------
TZ_UY = timezone(timedelta(hours=-3))

# ---------------------------------------------------------------------------
# Auth result templates
# ---------------------------------------------------------------------------
AUTH_LEGIT = {"spf": "pass", "dkim": "pass", "dmarc": "pass"}
AUTH_PHISHING = {"spf": "fail", "dkim": "fail", "dmarc": "fail"}
AUTH_BEC = {"spf": "pass", "dkim": "fail", "dmarc": "none"}
AUTH_NEUTRAL = {"spf": "neutral", "dkim": "none", "dmarc": "none"}

# ---------------------------------------------------------------------------
# Email templates (~65 emails)
# ---------------------------------------------------------------------------
# Each entry: (category, sender_email, sender_name, subject, body_text,
#              body_html, urls, attachments, auth_results_template, recipients_cc)
#
# Categories: legit, phishing, bec, malware

DEMO_EMAILS = [
    # ===== LEGITIMATE (~60%) =====
    # -- Internal / team communication --
    (
        "legit",
        "martin.rodriguez@strike.sh",
        "Martin Rodriguez",
        "Weekly sync - Sprint review",
        "Hola equipo,\n\nRecordatorio del weekly sync manana a las 10am. "
        "Vamos a revisar el progreso del sprint y planificar la siguiente iteracion.\n\n"
        "Agenda:\n- Demo de features completados\n- Blockers\n- Planning siguiente sprint\n\nSaludos,\nMartin",
        None,
        [],
        [],
        AUTH_LEGIT,
        ["team@strike.sh"],
    ),
    (
        "legit",
        "lucia.fernandez@strike.sh",
        "Lucia Fernandez",
        "Re: Revision de arquitectura - Pipeline v2",
        "Martin,\n\nRevise los cambios del pipeline. El approach de 3 capas "
        "se ve solido. Tengo algunas sugerencias menores sobre el manejo de timeouts "
        "en la capa LLM.\n\nPodemos discutirlo en el sync de manana?\n\nLucia",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "santiago.perez@strike.sh",
        "Santiago Perez",
        "Actualizacion de staging environment",
        "Team,\n\nDeploy de staging completado. Los cambios incluyen:\n"
        "- Fix de rate limiting en /api/v1/cases\n"
        "- Mejora de performance en queries de dashboard\n"
        "- Update de dependencias de seguridad\n\n"
        "Por favor verificar que todo funcione correctamente.\n\nSantiago",
        None,
        [],
        [],
        AUTH_LEGIT,
        ["devops@strike.sh"],
    ),
    (
        "legit",
        "carolina.martinez@strike.sh",
        "Carolina Martinez",
        "PTO Request - Semana del 17/02",
        "Hola,\n\nSolicito dias libres del 17 al 21 de febrero. "
        "Ya coordine con el equipo para cobertura.\n\nGracias,\nCarolina",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "diego.silva@strike.sh",
        "Diego Silva",
        "Resultados del penetration testing Q1",
        "Equipo,\n\nAdjunto el reporte del pentest de Q1. Resumen ejecutivo:\n"
        "- 0 vulnerabilidades criticas\n"
        "- 2 medias (ya parcheadas)\n"
        "- 5 bajas (informacionales)\n\n"
        "El reporte completo esta en el drive compartido.\n\nDiego",
        None,
        [],
        [{"filename": "pentest_q1_2025.pdf", "content_type": "application/pdf", "size": 245000}],
        AUTH_LEGIT,
        ["security@strike.sh"],
    ),
    # -- GitHub notifications --
    (
        "legit",
        "notifications@github.com",
        "GitHub",
        "[guardia] Pull Request #142: Fix heuristic scoring edge case",
        "rodrigo-miranda opened a pull request in strikesecurity/guardia\n\n"
        "Fix heuristic scoring edge case\n\n"
        "When auth_results are empty, the auth_score was NaN. "
        "This PR adds a fallback to 0.0.\n\n"
        "Files changed: 2\n+15 -3",
        None,
        ["https://github.com/strikesecurity/guardia/pull/142"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "notifications@github.com",
        "GitHub",
        "[guardia] Issue #89: Dashboard latency on large datasets",
        "lucia-fernandez opened an issue in strikesecurity/guardia\n\n"
        "Dashboard takes >3s to load when there are 500+ cases. "
        "The count query is doing a full table scan.\n\n"
        "Expected: <500ms load time\nActual: 3-5s",
        None,
        ["https://github.com/strikesecurity/guardia/issues/89"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "notifications@github.com",
        "GitHub",
        "[guardia-ml] New release: v1.2.1 - Model performance improvements",
        "Release v1.2.1\n\nChanges:\n"
        "- Improved F1 score from 0.91 to 0.94\n"
        "- Reduced inference time by 15%\n"
        "- Added support for multilingual inputs\n\n"
        "Full changelog: v1.2.0...v1.2.1",
        None,
        ["https://github.com/strikesecurity/guardia-ml/releases/tag/v1.2.1"],
        [],
        AUTH_LEGIT,
        [],
    ),
    # -- Google Workspace --
    (
        "legit",
        "calendar-notification@google.com",
        "Google Calendar",
        "Reminder: Thesis review meeting - Tomorrow 2:00 PM",
        "This is a reminder for your upcoming event.\n\n"
        "Thesis review meeting\nWhen: Tomorrow, 2:00 PM - 3:00 PM (UYT)\n"
        "Where: Google Meet (link attached)\n"
        "Attendees: Martin Rodriguez, Tutor ORT\n\n"
        "Join: https://meet.google.com/abc-defg-hij",
        None,
        ["https://meet.google.com/abc-defg-hij"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "drive-shares-dm-noreply@google.com",
        "Google Drive",
        "Santiago Perez shared a document: Guard-IA Architecture v2",
        "Santiago Perez has shared a document with you.\n\n"
        "Guard-IA Architecture v2\n\n"
        "Open in Google Docs: https://docs.google.com/document/d/1abc...\n\n"
        "This document contains the updated architecture diagrams.",
        None,
        ["https://docs.google.com/document/d/1abc"],
        [],
        AUTH_LEGIT,
        [],
    ),
    # -- External legitimate --
    (
        "legit",
        "billing@vercel.com",
        "Vercel",
        "Your Vercel invoice for January 2025",
        "Hi Strike Security,\n\nYour invoice for January 2025 is ready.\n\n"
        "Plan: Pro\nAmount: $20.00\nPeriod: Jan 1 - Jan 31, 2025\n\n"
        "View invoice: https://vercel.com/account/invoices\n\n"
        "Thanks for using Vercel.",
        None,
        ["https://vercel.com/account/invoices"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "noreply@neon.tech",
        "Neon",
        "Your Neon database usage report - January",
        "Hi,\n\nHere is your monthly usage report for project guardia_staging:\n\n"
        "Compute: 12.5 hours\nStorage: 256 MB\nData transfer: 1.2 GB\n\n"
        "All within free tier limits.\n\n"
        "View details: https://console.neon.tech/app/projects",
        None,
        ["https://console.neon.tech/app/projects"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "team@clerk.com",
        "Clerk",
        "Your Clerk usage summary",
        "Hi Strike Security,\n\nYour monthly authentication summary:\n\n"
        "Active users: 4\nSign-ins: 127\nSign-ups: 0\n\n"
        "View dashboard: https://dashboard.clerk.com",
        None,
        ["https://dashboard.clerk.com"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "invoices@cloudflare.com",
        "Cloudflare",
        "Cloudflare Invoice - February 2025",
        "Hello,\n\nYour Cloudflare invoice for February 2025 is available.\n\n"
        "Account: Strike Security\nPlan: Free\nDomains: strike.sh, guardia-sec.com\n"
        "Amount due: $0.00\n\n"
        "View invoice at https://dash.cloudflare.com/billing",
        None,
        ["https://dash.cloudflare.com/billing"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "no-reply@slack.com",
        "Slack",
        "New message in #guardia-alerts",
        "You have a new message in Strike Security workspace:\n\n"
        "#guardia-alerts\nPipeline alert: Email from suspicious domain "
        "paypa1-secure.xyz scored 0.87 (blocked)\n\n"
        "View in Slack: https://strikesecurity.slack.com/archives/C0AB9KN6Z",
        None,
        ["https://strikesecurity.slack.com/archives/C0AB9KN6Z"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "newsletter@pythonweekly.com",
        "Python Weekly",
        "Python Weekly - Issue #634",
        "Python Weekly Issue #634\n\n"
        "Articles:\n"
        "- FastAPI 0.110 released with new features\n"
        "- Understanding async SQLAlchemy patterns\n"
        "- Building ML pipelines with Python\n\n"
        "Tools:\n"
        "- ruff 0.3.0: Faster Python linter\n"
        "- structlog 24.1: Structured logging\n\n"
        "To unsubscribe: https://pythonweekly.com/unsubscribe",
        None,
        ["https://pythonweekly.com"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "support@linear.app",
        "Linear",
        "Re: [GUARD-45] Pipeline timeout on large emails",
        "Your issue GUARD-45 has been updated.\n\n"
        "Status: In Progress -> Done\n"
        "Assignee: Santiago Perez\n\n"
        "Comment: Fixed by increasing timeout to 30s and adding "
        "chunked processing for emails >100KB.\n\n"
        "View: https://linear.app/strike/issue/GUARD-45",
        None,
        ["https://linear.app/strike/issue/GUARD-45"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "noreply@sentry.io",
        "Sentry",
        "[guardia-backend] New issue: PipelineError in orchestrator.py",
        "New issue in guardia-backend\n\n"
        "PipelineError: LLM timeout after 10s\n"
        "orchestrator.py line 84 in analyze\n\n"
        "This issue has occurred 3 times in the last hour.\n"
        "First seen: 2 hours ago\n\n"
        "View: https://sentry.io/organizations/strike/issues/12345/",
        None,
        ["https://sentry.io/organizations/strike/issues/12345/"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "facturacion@antel.com.uy",
        "Antel",
        "Tu factura de febrero ya esta disponible",
        "Hola,\n\nTu factura de Antel para febrero 2025 esta lista.\n\n"
        "Monto: $1,890 (IVA incluido)\nVencimiento: 28/02/2025\n"
        "Plan: Fibra 300 Mbps\n\n"
        "Consulta tu factura en https://www.antel.com.uy/personas/mi-antel\n\n"
        "Antel - Conectamos a los uruguayos",
        None,
        ["https://www.antel.com.uy/personas/mi-antel"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "noreply@mercadolibre.com",
        "Mercado Libre",
        "Tu compra fue confirmada - Teclado Mecanico Keychron K2",
        "Hola Nicolas,\n\nTu compra fue confirmada.\n\n"
        "Producto: Teclado Mecanico Keychron K2 V2 Wireless\n"
        "Precio: $4,500\n"
        "Vendedor: TechStore UY\n"
        "Entrega estimada: 12-14 feb\n\n"
        "Seguir envio: https://www.mercadolibre.com.uy/mis-compras",
        None,
        ["https://www.mercadolibre.com.uy/mis-compras"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "info@ort.edu.uy",
        "Universidad ORT Uruguay",
        "Recordatorio: Entrega de avance de tesis - 15/02",
        "Estimado estudiante,\n\n"
        "Le recordamos que la fecha de entrega del avance de tesis es el "
        "15 de febrero de 2025.\n\n"
        "Requisitos:\n"
        "- Documento de avance (PDF)\n"
        "- Repositorio actualizado\n"
        "- Demo funcional\n\n"
        "Saludos cordiales,\nSecretaria Academica\nUniversidad ORT Uruguay",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "aws-marketing@amazon.com",
        "Amazon Web Services",
        "AWS re:Invent 2025 - Early bird registration open",
        "Register now for AWS re:Invent 2025\n\n"
        "Join us in Las Vegas, December 1-5, 2025\n"
        "Early bird pricing: $1,799\n\n"
        "Topics: AI/ML, Security, Serverless, and more.\n\n"
        "Register: https://reinvent.awsevents.com",
        None,
        ["https://reinvent.awsevents.com"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "soporte@pedidosya.com",
        "PedidosYa",
        "Tu pedido #78432 esta en camino",
        "Hola Nicolas!\n\nTu pedido esta en camino.\n\n"
        "Restaurante: Burger Town\n"
        "Pedido: 1x Classic Burger + Papas\n"
        "Delivery estimado: 35-45 min\n\n"
        "Seguir pedido: https://www.pedidosya.com.uy/tracking",
        None,
        ["https://www.pedidosya.com.uy/tracking"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "security@github.com",
        "GitHub",
        "[GitHub] Dependabot alert: High severity vulnerability in axios",
        "A new Dependabot alert was found in strikesecurity/guardia.\n\n"
        "Package: axios\nSeverity: High\nVulnerability: CVE-2024-XXXXX - SSRF in proxy\n\n"
        "Affected versions: < 1.7.4\nPatched version: 1.7.4\n\n"
        "View alert: https://github.com/strikesecurity/guardia/security/dependabot/1",
        None,
        ["https://github.com/strikesecurity/guardia/security/dependabot/1"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "hello@resend.com",
        "Resend",
        "Your API key was used from a new IP address",
        "Hi,\n\nYour Resend API key (re_...abc) was used from a new IP address:\n\n"
        "IP: 34.95.xx.xx (GCP, South America)\n"
        "Time: 2025-02-08 14:23 UTC\n\n"
        "If this was you, no action needed. Otherwise, rotate your key at "
        "https://resend.com/api-keys",
        None,
        ["https://resend.com/api-keys"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "noreply@notion.so",
        "Notion",
        "Santiago mentioned you in Guard-IA Roadmap",
        "Santiago Perez mentioned you in a comment:\n\n"
        "'@nico revisa la seccion de deployment, actualice los pasos para Cloud Run.'\n\n"
        "Page: Guard-IA Roadmap > Deployment Guide\n\n"
        "View in Notion: https://notion.so/strike/guardia-roadmap",
        None,
        ["https://notion.so/strike/guardia-roadmap"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "receipts@stripe.com",
        "Stripe",
        "Your payment to OpenAI was successful",
        "Payment confirmation\n\n"
        "Amount: $12.47\n"
        "Description: OpenAI API usage - January 2025\n"
        "Card: Visa ending in 4242\n"
        "Date: February 1, 2025\n\n"
        "View receipt: https://pay.stripe.com/receipts/abc123",
        None,
        ["https://pay.stripe.com/receipts/abc123"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "martin.rodriguez@strike.sh",
        "Martin Rodriguez",
        "Feedback sobre la demo de manana",
        "Nico,\n\nRevise la version staging y se ve muy bien. "
        "Algunas sugerencias para la demo:\n\n"
        "1. Arrancar por el dashboard general\n"
        "2. Mostrar un caso de phishing detectado\n"
        "3. Hacer la demo en vivo al final\n\n"
        "Suerte manana!\nMartin",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "jira@strikesecurity.atlassian.net",
        "Jira",
        "[GUARD-78] Story completed: LLM floor/cap implementation",
        "Santiago Perez updated GUARD-78\n\n"
        "Status: In Review -> Done\n"
        "Story Points: 5\n\n"
        "Summary: Implement LLM floor and cap adjustments to final score\n"
        "Resolution: Done\n\n"
        "View: https://strikesecurity.atlassian.net/browse/GUARD-78",
        None,
        ["https://strikesecurity.atlassian.net/browse/GUARD-78"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "notifications@github.com",
        "GitHub",
        "[guardia] CI: All checks passed on main",
        "All checks have passed on main branch.\n\n"
        "Commit: a1b2c3d Fix heuristic scoring edge case\n"
        "Author: rodrigo-miranda\n\n"
        "Checks:\n"
        "- pytest: passed (142 tests)\n"
        "- ruff: passed\n"
        "- vitest: passed (38 tests)\n"
        "- deploy-staging: success",
        None,
        ["https://github.com/strikesecurity/guardia/actions/runs/12345"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "lucia.fernandez@strike.sh",
        "Lucia Fernandez",
        "Paper de referencia - Email threat detection with transformers",
        "Nico,\n\nEncontre este paper que puede servir para la tesis:\n\n"
        "'Email Threat Detection Using Fine-Tuned Transformer Models'\n"
        "Autores: Zhang et al., 2024\n"
        "Publicado en: IEEE S&P\n\n"
        "Tiene un approach similar al nuestro con DistilBERT. "
        "La seccion 4 sobre feature engineering es muy relevante.\n\n"
        "https://arxiv.org/abs/2024.xxxxx\n\nLucia",
        None,
        ["https://arxiv.org/abs/2024.xxxxx"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "vendors@contoso.com",
        "Contoso Ltd",
        "Invoice #INV-2025-0234 - Consulting services January",
        "Dear Strike Security,\n\n"
        "Please find below the invoice for consulting services rendered in January 2025.\n\n"
        "Invoice: INV-2025-0234\nAmount: USD 3,500.00\nDue date: February 28, 2025\n"
        "Payment terms: Net 30\n\n"
        "Bank details attached.\n\nBest regards,\nAccounts Receivable\nContoso Ltd",
        None,
        [],
        [{"filename": "INV-2025-0234.pdf", "content_type": "application/pdf", "size": 89000}],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "no-reply@google.com",
        "Google Workspace",
        "Security alert: New sign-in to your Google Account",
        "New sign-in to nico@guardia-sec.com\n\n"
        "We noticed a new sign-in to your Google Account.\n\n"
        "Device: MacBook Pro\nLocation: Montevideo, Uruguay\n"
        "Time: February 8, 2025, 9:15 AM UYT\n\n"
        "If this was you, you can disregard this email.\n"
        "If not, review your account at https://myaccount.google.com/security",
        None,
        ["https://myaccount.google.com/security"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "hello@cal.com",
        "Cal.com",
        "New booking: Thesis advisor meeting",
        "New booking confirmed\n\n"
        "Event: Thesis advisor meeting\n"
        "Date: February 12, 2025\n"
        "Time: 3:00 PM - 3:30 PM (UYT)\n"
        "Location: Google Meet\n\n"
        "Attendees: Nicolas, Prof. Garcia\n\n"
        "Manage booking: https://cal.com/bookings",
        None,
        ["https://cal.com/bookings"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "noreply@docker.com",
        "Docker",
        "Docker Hub: Image push successful - guardia-backend:staging",
        "Image pushed successfully\n\n"
        "Repository: strikesecurity/guardia-backend\n"
        "Tag: staging\n"
        "Size: 245 MB\n"
        "Digest: sha256:abc123...\n\n"
        "View: https://hub.docker.com/r/strikesecurity/guardia-backend",
        None,
        ["https://hub.docker.com/r/strikesecurity/guardia-backend"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "santiago.perez@strike.sh",
        "Santiago Perez",
        "Re: Monitoreo de pipeline - metricas de la semana",
        "Team,\n\nResumen de metricas del pipeline esta semana:\n\n"
        "- Emails procesados: 847\n"
        "- Latencia promedio: 4.2s\n"
        "- Amenazas detectadas: 23 (2.7%)\n"
        "- Falsos positivos reportados: 1\n"
        "- Uptime: 99.8%\n\n"
        "El unico FP fue un newsletter de Python Weekly que tenia "
        "muchos links. Ya ajuste el threshold.\n\nSantiago",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "no-reply@openai.com",
        "OpenAI",
        "Your OpenAI API usage report - January 2025",
        "Hi,\n\nHere's your API usage for January 2025:\n\n"
        "Model: gpt-4o-mini\n"
        "Requests: 2,847\n"
        "Tokens: 1.2M input, 340K output\n"
        "Cost: $12.47\n\n"
        "View details: https://platform.openai.com/usage",
        None,
        ["https://platform.openai.com/usage"],
        [],
        AUTH_LEGIT,
        [],
    ),
    # ===== PHISHING (~25%) =====
    (
        "phishing",
        "security@paypa1-secure.com",
        "PayPal Security Team",
        "URGENT: Your PayPal account has been limited",
        "Dear Customer,\n\n"
        "We have detected unusual activity on your PayPal account. "
        "Your account has been temporarily limited.\n\n"
        "To restore full access, please verify your identity immediately:\n"
        "https://paypa1-secure.com/verify-account?id=x7k2m\n\n"
        "If you do not verify within 24 hours, your account will be permanently suspended.\n\n"
        "PayPal Security Team",
        None,
        ["https://paypa1-secure.com/verify-account?id=x7k2m"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "noreply@micr0soft-365.com",
        "Microsoft 365",
        "Action Required: Your Office 365 password expires today",
        "Your Office 365 password will expire today.\n\n"
        "To avoid losing access to your email and files, "
        "update your password now:\n\n"
        "https://micr0soft-365.com/password-reset\n\n"
        "This is an automated message from Microsoft 365 Admin.\n"
        "Do not reply to this email.",
        None,
        ["https://micr0soft-365.com/password-reset"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "alert@amazon-security-center.net",
        "Amazon",
        "Your Amazon order #302-4829173-8827465 has a problem",
        "Hello,\n\n"
        "We encountered an issue processing your recent order.\n"
        "Your payment method was declined.\n\n"
        "Order: #302-4829173-8827465\n"
        "Item: MacBook Pro 16\"\n"
        "Amount: $2,499.00\n\n"
        "Update your payment information:\n"
        "https://amazon-security-center.net/update-payment\n\n"
        "If you did not place this order, click here to cancel.",
        None,
        ["https://amazon-security-center.net/update-payment"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "admin@g00gle-workspace.com",
        "Google Workspace Admin",
        "Immediate action required: Storage quota exceeded",
        "Dear User,\n\n"
        "Your Google Workspace storage has reached 100% capacity. "
        "Emails and files will stop syncing in 12 hours.\n\n"
        "Upgrade your storage immediately:\n"
        "https://g00gle-workspace.com/upgrade-storage\n\n"
        "Current usage: 15.0 GB / 15.0 GB\n\n"
        "Google Workspace Team",
        None,
        ["https://g00gle-workspace.com/upgrade-storage"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "shipping@fedex-tracking.xyz",
        "FedEx",
        "Your package could not be delivered - Action required",
        "Dear Customer,\n\n"
        "We attempted to deliver your package today but no one was available.\n\n"
        "Tracking Number: 7489 2310 4567\n"
        "Scheduled: February 7, 2025\n\n"
        "To reschedule delivery, confirm your address:\n"
        "https://fedex-tracking.xyz/reschedule?t=7489231045\n\n"
        "If not rescheduled within 48 hours, the package will be returned to sender.\n\n"
        "FedEx Customer Service",
        None,
        ["https://fedex-tracking.xyz/reschedule?t=7489231045"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "support@netflix-billing-update.com",
        "Netflix",
        "Your Netflix membership has been suspended",
        "Hi,\n\n"
        "We were unable to process your last payment. "
        "Your Netflix membership has been suspended.\n\n"
        "To continue watching, update your billing information:\n"
        "https://netflix-billing-update.com/reactivate\n\n"
        "Current plan: Premium 4K\nLast charge attempt: $22.99\n\n"
        "If not resolved in 48 hours, your account and viewing history will be deleted.\n\n"
        "The Netflix Team",
        None,
        ["https://netflix-billing-update.com/reactivate"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "postmaster@dropbox-share.info",
        "Dropbox",
        "Document shared with you: Q4_Financial_Report.pdf",
        "Hi,\n\n"
        "Martin Rodriguez shared a file with you on Dropbox.\n\n"
        "Q4_Financial_Report.pdf (2.4 MB)\n\n"
        "View document: https://dropbox-share.info/view/q4-report\n\n"
        "This link expires in 7 days.\n\n"
        "Dropbox - Securely share and access files anywhere",
        None,
        ["https://dropbox-share.info/view/q4-report"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "helpdesk@1inkedin-security.com",
        "LinkedIn",
        "Your LinkedIn account may have been compromised",
        "Dear User,\n\n"
        "We detected a login from an unrecognized device:\n\n"
        "Device: Windows PC\n"
        "Location: Lagos, Nigeria\n"
        "Time: February 9, 2025 03:22 AM\n\n"
        "If this wasn't you, secure your account immediately:\n"
        "https://1inkedin-security.com/secure-account\n\n"
        "LinkedIn Security Team",
        None,
        ["https://1inkedin-security.com/secure-account"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "no-reply@apple-id-verify.net",
        "Apple",
        "Your Apple ID has been locked for security reasons",
        "Dear Customer,\n\n"
        "Your Apple ID (n***@strike.sh) has been locked due to "
        "multiple failed sign-in attempts.\n\n"
        "To unlock your account, verify your identity:\n"
        "https://apple-id-verify.net/unlock\n\n"
        "If you don't verify within 24 hours, your account will be permanently disabled.\n\n"
        "Apple Support",
        None,
        ["https://apple-id-verify.net/unlock"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "billing@stripe-invoice.cc",
        "Stripe",
        "Failed payment: Invoice #INV-83921 requires attention",
        "A payment attempt for your Stripe account has failed.\n\n"
        "Invoice: #INV-83921\n"
        "Amount: $487.50\n"
        "Reason: Card declined\n\n"
        "Update your payment method to avoid service interruption:\n"
        "https://stripe-invoice.cc/update-billing\n\n"
        "Stripe Billing",
        None,
        ["https://stripe-invoice.cc/update-billing"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "award@international-grant.org",
        "International Research Foundation",
        "Congratulations! Your research proposal has been selected",
        "Dear Researcher,\n\n"
        "We are pleased to inform you that your research proposal "
        "has been selected for a $25,000 grant.\n\n"
        "To claim your grant, please provide your details:\n"
        "https://international-grant.org/claim-grant?ref=URY2025\n\n"
        "Required information:\n"
        "- Full name\n"
        "- Bank account details\n"
        "- University affiliation\n\n"
        "International Research Foundation",
        None,
        ["https://international-grant.org/claim-grant?ref=URY2025"],
        [],
        AUTH_NEUTRAL,
        [],
    ),
    # ===== BEC (~10%) =====
    (
        "bec",
        "martin.rodriguez@str1ke.sh",
        "Martin Rodriguez",
        "Urgent - Wire transfer needed today",
        "Nico,\n\n"
        "Necesito que hagas una transferencia urgente hoy. "
        "Es para cerrar el deal con el nuevo cliente.\n\n"
        "Monto: USD 15,000\n"
        "Cuenta: Wells Fargo 4839201847\n"
        "Routing: 121000248\n"
        "Beneficiario: TechPartners LLC\n\n"
        "Es urgente, necesito que lo hagas antes de las 3pm.\n"
        "No me llames, estoy en reuniones todo el dia.\n\n"
        "Martin",
        None,
        [],
        [],
        AUTH_BEC,
        [],
    ),
    (
        "bec",
        "ceo@str1ke.sh",
        "CEO - Strike Security",
        "Confidential - Acquisition payment",
        "Hi,\n\n"
        "I need you to process a confidential payment for an acquisition "
        "we're finalizing. This is time-sensitive.\n\n"
        "Amount: USD 45,000\n"
        "Wire to: First National Bank\n"
        "Account: 2847193650\n"
        "Reference: ACQ-2025-CONF\n\n"
        "Please handle this discreetly. Do not discuss with other team members.\n\n"
        "Thanks",
        None,
        [],
        [],
        AUTH_BEC,
        [],
    ),
    (
        "bec",
        "accounting@str1ke.sh",
        "Strike Security Accounting",
        "Updated bank details - Vendor payment redirect",
        "Dear Finance Team,\n\n"
        "Please note our banking details have changed effective immediately.\n\n"
        "All pending payments should be redirected to:\n"
        "Bank: Citibank\n"
        "Account: 8273910456\n"
        "Routing: 021000089\n"
        "Account Name: Strike Security Holdings\n\n"
        "Please update your records and process the outstanding invoice "
        "of $8,750 to the new account.\n\n"
        "Regards,\nAccounting Department",
        None,
        [],
        [],
        AUTH_BEC,
        [],
    ),
    (
        "bec",
        "lucia.fernandez@str1ke.sh",
        "Lucia Fernandez",
        "Can you help me with something? (confidential)",
        "Nico,\n\n"
        "Estoy en una reunion y no puedo hablar. Necesito que compres "
        "gift cards de Amazon por un total de $2,000 para un evento "
        "sorpresa del equipo.\n\n"
        "Compra 4 tarjetas de $500 cada una y mandame los codigos "
        "por email.\n\n"
        "Te reembolso manana. Es urgente.\n\n"
        "Gracias,\nLucia",
        None,
        [],
        [],
        AUTH_BEC,
        [],
    ),
    (
        "bec",
        "admin@strlke.sh",
        "IT Admin - Strike Security",
        "Password reset required - Security compliance",
        "Dear employee,\n\n"
        "As part of our quarterly security compliance review, "
        "all employees must reset their passwords.\n\n"
        "Please reset your password using our internal portal:\n"
        "https://sso.strlke.sh/reset-password\n\n"
        "This must be completed by end of day.\n\n"
        "IT Security Team\nStrike Security",
        None,
        ["https://sso.strlke.sh/reset-password"],
        [],
        AUTH_BEC,
        [],
    ),
    # ===== MALWARE (~5%) =====
    (
        "malware",
        "scanner@docusign-notify.com",
        "DocuSign",
        "Document ready for signature: NDA_StrikeSecurity_2025.pdf",
        "Hi,\n\n"
        "A document requires your electronic signature.\n\n"
        "Document: NDA_StrikeSecurity_2025.pdf\n"
        "Sender: Legal Department\n\n"
        "Review and sign: https://docusign-notify.com/sign/abc123\n\n"
        "Or download the document directly from the attachment.\n\n"
        "DocuSign - The way the world agrees",
        None,
        ["https://docusign-notify.com/sign/abc123"],
        [
            {
                "filename": "NDA_StrikeSecurity_2025.pdf.exe",
                "content_type": "application/x-msdownload",
                "size": 892000,
            }
        ],
        AUTH_PHISHING,
        [],
    ),
    (
        "malware",
        "finance@vendor-invoicing.net",
        "Vendor Invoicing",
        "Invoice #8847 - Payment overdue",
        "Dear Accounts Payable,\n\n"
        "Please find attached the overdue invoice for services rendered.\n\n"
        "Invoice: #8847\n"
        "Amount: $6,250.00\n"
        "Due: January 30, 2025 (OVERDUE)\n\n"
        "Please process payment immediately to avoid late fees.\n\n"
        "See attached invoice for bank details.\n\n"
        "Regards,\nVendor Invoicing Department",
        None,
        [],
        [
            {
                "filename": "Invoice_8847.xlsm",
                "content_type": "application/vnd.ms-excel.sheet.macroEnabled.12",
                "size": 456000,
            }
        ],
        AUTH_PHISHING,
        [],
    ),
    (
        "malware",
        "hr-updates@strike-careers.com",
        "HR Department",
        "Updated employee handbook - Please review",
        "Dear Team,\n\n"
        "We have updated the employee handbook with new policies "
        "effective March 1, 2025.\n\n"
        "Key changes:\n"
        "- Remote work policy update\n"
        "- New PTO accrual rules\n"
        "- Updated code of conduct\n\n"
        "Please download and review the attached document.\n\n"
        "HR Department",
        None,
        [],
        [
            {
                "filename": "Employee_Handbook_2025.docm",
                "content_type": "application/vnd.ms-word.document.macroEnabled.12",
                "size": 1250000,
            }
        ],
        AUTH_NEUTRAL,
        [],
    ),
    # ===== ADDITIONAL LEGITIMATE (to reach ~65) =====
    (
        "legit",
        "diego.silva@strike.sh",
        "Diego Silva",
        "Onboarding checklist - Nuevo integrante",
        "Team,\n\nLa semana que viene se incorpora Valentina al equipo de security.\n\n"
        "Checklist de onboarding:\n"
        "- [ ] Cuenta de Google Workspace\n"
        "- [ ] Acceso a GitHub org\n"
        "- [ ] Credenciales de staging\n"
        "- [ ] Reunion de bienvenida\n\n"
        "Por favor completen los items que les corresponden.\n\nDiego",
        None,
        [],
        [],
        AUTH_LEGIT,
        ["hr@strike.sh"],
    ),
    (
        "legit",
        "noreply@figma.com",
        "Figma",
        "Carolina left a comment on Guard-IA Dashboard Mockup",
        "Carolina Martinez left a comment:\n\n"
        "'El color del badge de riesgo critico deberia ser mas oscuro "
        "para mejor contraste. Tambien sugiero agregar un tooltip con el score exacto.'\n\n"
        "File: Guard-IA Dashboard Mockup v3\n"
        "View: https://figma.com/file/abc123/guardia-dashboard",
        None,
        ["https://figma.com/file/abc123/guardia-dashboard"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "notifications@github.com",
        "GitHub",
        "[guardia] PR Review: santiago-perez approved #142",
        "santiago-perez approved this pull request.\n\n"
        "LGTM! The edge case fix looks good. Just one minor suggestion:\n"
        "consider adding a unit test for the empty auth_results case.\n\n"
        "View: https://github.com/strikesecurity/guardia/pull/142#pullrequestreview-abc",
        None,
        ["https://github.com/strikesecurity/guardia/pull/142"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "no-reply@zoom.us",
        "Zoom",
        "Cloud recording available: Thesis defense rehearsal",
        "Hi Nicolas,\n\n"
        "Your cloud recording is now available.\n\n"
        "Meeting: Thesis defense rehearsal\n"
        "Date: February 7, 2025\n"
        "Duration: 42 minutes\n\n"
        "View recording: https://zoom.us/rec/share/abc123\n"
        "Recording will be available for 30 days.",
        None,
        ["https://zoom.us/rec/share/abc123"],
        [],
        AUTH_LEGIT,
        [],
    ),
    (
        "legit",
        "martin.rodriguez@strike.sh",
        "Martin Rodriguez",
        "Re: Presupuesto Q2 - herramientas de seguridad",
        "Team,\n\nAprobado el presupuesto para las siguientes herramientas:\n\n"
        "- Sentry (Pro): $26/mes\n"
        "- Vercel (Pro): $20/mes\n"
        "- OpenAI API: ~$15/mes estimado\n"
        "- Neon (Free tier)\n\n"
        "Total estimado: $61/mes. Dentro del presupuesto asignado.\n\nMartin",
        None,
        [],
        [],
        AUTH_LEGIT,
        [],
    ),
    # Additional phishing
    (
        "phishing",
        "security-alert@wells-farg0.com",
        "Wells Fargo Security",
        "Suspicious transaction on your account - Verify now",
        "Dear Customer,\n\n"
        "A suspicious transaction was detected on your account:\n\n"
        "Amount: $1,247.00\n"
        "Merchant: Electronics Store\n"
        "Location: Moscow, Russia\n"
        "Date: February 9, 2025\n\n"
        "If you did not authorize this transaction, verify immediately:\n"
        "https://wells-farg0.com/verify-transaction\n\n"
        "Wells Fargo Fraud Protection",
        None,
        ["https://wells-farg0.com/verify-transaction"],
        [],
        AUTH_PHISHING,
        [],
    ),
    (
        "phishing",
        "support@slack-workspace.net",
        "Slack",
        "Your Slack workspace requires re-authentication",
        "Hi,\n\n"
        "Due to a security update, all members of Strike Security workspace "
        "need to re-authenticate their accounts.\n\n"
        "Re-authenticate now:\n"
        "https://slack-workspace.net/reauth?team=strikesecurity\n\n"
        "Your access will be revoked in 6 hours if not completed.\n\n"
        "Slack Security Team",
        None,
        ["https://slack-workspace.net/reauth?team=strikesecurity"],
        [],
        AUTH_PHISHING,
        [],
    ),
    # Additional BEC
    (
        "bec",
        "diego.silva@str1ke.sh",
        "Diego Silva",
        "Cambio de cuenta bancaria - nomina",
        "Hola,\n\n"
        "Cambie de banco y necesito actualizar mis datos para "
        "el deposito de nomina.\n\n"
        "Nuevo banco: Santander\n"
        "Cuenta: 0012-3456-78\n"
        "Titular: Diego Silva\n\n"
        "Por favor actualizar antes del cierre de este mes.\n\n"
        "Gracias,\nDiego",
        None,
        [],
        [],
        AUTH_BEC,
        [],
    ),
    # Additional malware
    (
        "malware",
        "shared@wetransfer-files.com",
        "WeTransfer",
        "You received files: Project_Assets.zip",
        "Hi,\n\n"
        "martin.rodriguez@strike.sh sent you files via WeTransfer.\n\n"
        "Files: Project_Assets.zip (48 MB)\n"
        "Expires: February 15, 2025\n\n"
        "Download: https://wetransfer-files.com/download/abc123\n\n"
        "Get your files now before they expire.",
        None,
        ["https://wetransfer-files.com/download/abc123"],
        [
            {
                "filename": "Project_Assets.zip",
                "content_type": "application/zip",
                "size": 48000000,
            }
        ],
        AUTH_PHISHING,
        [],
    ),
]

# Recipient pool for demo
RECIPIENTS = [
    "nico@guardia-sec.com",
    "nico@strike.sh",
    "security@strike.sh",
    "team@strike.sh",
    "admin@strike.sh",
]


def _generate_message_id(sender_email: str, idx: int) -> str:
    """Generate a realistic RFC 5322 Message-ID."""
    domain = sender_email.split("@")[1] if "@" in sender_email else "unknown.com"
    uid = uuid4().hex[:12]
    return f"<{uid}.{idx}@{domain}>"


def _generate_headers(sender_email: str, sender_name: str, recipient: str, dt: datetime) -> dict:
    """Generate realistic email headers."""
    domain = sender_email.split("@")[1] if "@" in sender_email else "unknown.com"
    return {
        "From": f"{sender_name} <{sender_email}>" if sender_name else sender_email,
        "To": recipient,
        "Date": dt.strftime("%a, %d %b %Y %H:%M:%S %z"),
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "X-Mailer": "SMTP Gateway",
        "Received": f"from {domain} (mail.{domain} [198.51.100.{random.randint(1, 254)}])",
    }


def _distribute_timestamps(count: int, days: int = 7) -> list[datetime]:
    """Distribute timestamps across `days` days, 8am-6pm UY time, more on weekdays."""
    now = datetime.now(TZ_UY)
    timestamps = []

    # Generate per-day counts (more on weekdays)
    day_slots = []
    for d in range(days):
        day = now - timedelta(days=days - 1 - d)
        weekday = day.weekday()
        if weekday < 5:  # Mon-Fri
            day_slots.append((day, random.randint(8, 14)))
        else:  # Sat-Sun
            day_slots.append((day, random.randint(3, 6)))

    # Normalize to match total count
    total_raw = sum(c for _, c in day_slots)
    day_slots_normalized = []
    for day, c in day_slots:
        normalized = max(1, round(c * count / total_raw))
        day_slots_normalized.append((day, normalized))

    # Adjust to match exact count
    current_total = sum(c for _, c in day_slots_normalized)
    diff = count - current_total
    if diff > 0:
        for i in range(diff):
            idx = i % len(day_slots_normalized)
            d, c = day_slots_normalized[idx]
            day_slots_normalized[idx] = (d, c + 1)
    elif diff < 0:
        for i in range(-diff):
            idx = len(day_slots_normalized) - 1 - (i % len(day_slots_normalized))
            d, c = day_slots_normalized[idx]
            if c > 1:
                day_slots_normalized[idx] = (d, c - 1)

    # Generate timestamps for each day
    for day, emails_count in day_slots_normalized:
        for _ in range(emails_count):
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            ts = day.replace(hour=hour, minute=minute, second=second, microsecond=0)
            timestamps.append(ts)

    timestamps.sort()
    return timestamps[:count]


async def clean_data(session) -> None:
    """Delete all existing demo data (evidence -> analysis -> case -> email)."""
    print("Cleaning existing data...")
    await session.execute(delete(Evidence))
    await session.execute(delete(Analysis))
    await session.execute(delete(Case))
    await session.execute(delete(Email))
    await session.commit()
    # Reset case_number sequence
    await session.execute(text("ALTER SEQUENCE IF EXISTS case_number_seq RESTART WITH 1"))
    await session.commit()
    print("  Done - all tables cleaned")


async def seed_emails(session, timestamps: list[datetime]) -> list[Email]:
    """Create Email records from DEMO_EMAILS with distributed timestamps."""
    emails_to_create = DEMO_EMAILS[:len(timestamps)]
    created = []

    for idx, (template, ts) in enumerate(zip(emails_to_create, timestamps)):
        category, sender_email, sender_name, subject, body_text, body_html, \
            urls, attachments, auth_tpl, recipients_cc = template

        # Pick recipient - mostly nico@guardia-sec.com for demo
        if idx % 5 == 0 and idx > 0:
            recipient = random.choice(RECIPIENTS[1:])
        else:
            recipient = RECIPIENTS[0]

        # Auth results are flat strings: {"spf": "pass", "dkim": "fail", ...}
        auth_results = dict(auth_tpl)

        email = Email(
            message_id=_generate_message_id(sender_email, idx),
            sender_email=sender_email,
            sender_name=sender_name,
            recipient_email=recipient,
            recipients_cc=recipients_cc,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            headers=_generate_headers(sender_email, sender_name, recipient, ts),
            urls=urls,
            attachments=attachments,
            auth_results=auth_results,
            received_at=ts,
        )
        session.add(email)
        created.append(email)

    await session.flush()
    print(f"  Created {len(created)} emails")
    return created


async def run_pipeline(session, emails: list[Email]) -> None:
    """Run the detection pipeline on each email."""
    orchestrator = PipelineOrchestrator(session)

    success = 0
    failed = 0

    for i, email in enumerate(emails, 1):
        try:
            result = await orchestrator.analyze(email.id)
            await session.commit()
            verdict = result.verdict
            score = result.final_score
            print(
                f"  [{i}/{len(emails)}] {email.sender_email[:30]:30s} "
                f"-> score={score:.2f} verdict={verdict}"
            )
            success += 1
        except Exception as exc:
            failed += 1
            print(f"  [{i}/{len(emails)}] FAILED {email.sender_email}: {exc}")
            await session.rollback()

    print(f"\n  Pipeline results: {success} ok, {failed} failed")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for Guard-IA")
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="Skip running detection pipeline (only create emails)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete all existing data before seeding",
    )
    args = parser.parse_args()

    count = len(DEMO_EMAILS)
    print(f"Guard-IA Demo Seed: {count} emails over 7 days")
    print(f"  Pipeline: {'skip' if args.no_pipeline else 'enabled'}")
    print(f"  Clean: {'yes' if args.clean else 'no'}")
    print()

    async with async_session_factory() as session:
        if args.clean:
            await clean_data(session)

        # Generate distributed timestamps
        timestamps = _distribute_timestamps(count, days=7)
        print(f"Timestamp range: {timestamps[0].isoformat()} to {timestamps[-1].isoformat()}")

        # Seed emails
        print("\nCreating emails...")
        emails = await seed_emails(session, timestamps)
        await session.commit()

        # Run pipeline
        if not args.no_pipeline:
            print("\nRunning pipeline (this may take a few minutes with LLM calls)...")
            await run_pipeline(session, emails)

            # Sync timestamps: set cases/analyses/evidences created_at to email received_at
            # so the dashboard trend chart shows distributed data across 7 days.
            print("\nSyncing timestamps to match email dates...")
            await session.execute(text(
                "UPDATE cases SET created_at = e.received_at, updated_at = e.received_at "
                "FROM emails e WHERE e.id = cases.email_id"
            ))
            await session.execute(text(
                "UPDATE analyses SET created_at = e.received_at "
                "FROM emails e JOIN cases c ON c.email_id = e.id "
                "WHERE analyses.case_id = c.id"
            ))
            await session.execute(text(
                "UPDATE evidences SET created_at = e.received_at "
                "FROM emails e JOIN cases c ON c.email_id = e.id "
                "JOIN analyses a ON a.case_id = c.id "
                "WHERE evidences.analysis_id = a.id"
            ))
            await session.commit()
            print("  Timestamps synced")

    # Summary
    categories = {}
    for tpl in DEMO_EMAILS[:count]:
        cat = tpl[0]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nSeed complete!")
    print(f"  Total emails: {count}")
    for cat, n in sorted(categories.items()):
        pct = n / count * 100
        print(f"  {cat}: {n} ({pct:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())
