# Guard-IA v0.2 — Estado Actual y Roadmap

## Objetivo del Release v0.2

> Mejorar la clasificación de los correos electrónicos interceptados y brindar más información sobre los datos procesados.

---

## 1. Estado Actual por Objetivo v0.2

### 1.1 Integración con Gmail/Google Workspace en entorno controlado

| Componente | Estado | Detalle |
|---|---|---|
| SMTP Gateway (aiosmtpd, puerto 2525) | ✅ Completo | `app/gateway/server.py`, `handler.py` — Recibe emails vía SMTP, procesa pipeline, decide verdict |
| Email Parser (RFC 5322) | ✅ Completo | `app/gateway/parser.py` — Extrae headers, body, URLs, attachments, auth results |
| Relay a Google (aspmx.l.google.com) | ✅ Completo | `app/gateway/relay.py` — Forward con headers X-Guard-IA-*, TLS, fail-open |
| Dominio de pruebas (strike.sh) | ✅ Configurado | `accepted_domains: "strike.sh"` en config |
| Simulador de emails | ✅ Completo | `scripts/simulate_email.py` + 6 templates realistas (clean, phishing, BEC, malware, spear, newsletter) |
| **Ruteo real desde Google Workspace** | ❌ Pendiente | No hay configuración de inbound gateway en Google Admin. Actualmente solo funciona con el simulador local |
| **Recepción de copia de correos (journal/routing rules)** | ❌ Pendiente | Falta configurar routing rules en Google Workspace para redirigir copia de emails al gateway |

**Resumen**: La infraestructura técnica está 100% lista. Falta la configuración del lado de Google Workspace para rutear correos reales al gateway.

---

### 1.2 Primer modelo de clasificación (IA/ML baseline + reglas)

| Componente | Estado | Detalle |
|---|---|---|
| Motor heurístico (4 sub-engines) | ✅ Completo | Domain analysis, URL analysis, Keyword analysis, Auth analysis — Cada uno pesa 25% |
| Tipado de amenazas | ✅ Completo | BEC, credential_phishing, malware_payload, generic_phishing, clean |
| Generación de evidencias | ✅ Completo | 12+ tipos de evidencia (typosquatting, URL shortener, IP-based URL, SPF/DKIM/DMARC fail, urgency keywords, etc.) |
| Whitelist/Blacklist integrada | ✅ Completo | `policy_service.py` — Bypass de heurísticas para dominios whitelistados |
| Código de inferencia DistilBERT | ✅ Completo | `ml_classifier.py` — Singleton, lazy load, graceful degradation |
| Código de entrenamiento | ✅ Completo | `ml/src/train.py` — Fine-tune DistilBERT, MLflow tracking, early stopping |
| Código de preprocesamiento | ✅ Completo | `ml/src/preprocess.py` — Carga CSV, limpieza, split estratificado 80/10/10 |
| **Modelo entrenado (weights)** | ❌ Pendiente | `ml/models/distilbert-guardia/` solo tiene `.gitkeep` — No hay weights ni tokenizer |
| **Dataset de entrenamiento** | ❌ Pendiente | `ml/data/` vacío — Falta dataset de phishing para entrenar |
| **Ponderación ML+Heurísticas** | ✅ Listo (inactivo) | Configurado: 40% heurísticas + 60% ML. Actualmente cae a 100% heurísticas porque el modelo no existe |
| LLM Explainer (Claude + GPT fallback) | ✅ Completo | `llm_explainer.py` — Solo explica, no decide. Funciona pero requiere API keys configuradas |

**Resumen**: El framework completo de ML está implementado end-to-end (training → inference → pipeline integration). Falta ejecutar: conseguir dataset, entrenar modelo, deployar weights.

---

### 1.3 Acciones automáticas iniciales

| Componente | Estado | Detalle |
|---|---|---|
| Quarantine automática (score ≥ 0.8) | ✅ Completo | Gateway almacena raw email en disco, case marcado como QUARANTINED |
| Warning headers (0.3 ≤ score < 0.6) | ✅ Completo | Relay inyecta `X-Guard-IA-Warning: true` al forward a Google |
| Block/Reject (score ≥ 0.8) | ✅ Completo | Gateway retorna SMTP 550 reject |
| Quarantine management (release/keep/delete) | ✅ Completo | `quarantine_service.py` — CISO puede liberar, mantener o eliminar emails |
| Alert rules engine | ✅ Completo | `alert_service.py` — Reglas por score, verdict, risk_level, threat_category. CRUD completo + evaluación |
| **Entrega de alertas (email/Slack)** | ❌ Pendiente | El engine evalúa reglas y persiste AlertEvents, pero no hay worker que envíe emails/Slack |
| **Etiquetado en Gmail (labels)** | ❌ Pendiente | No hay integración con Gmail Labels API para marcar emails como sospechosos |
| **Mover a carpeta en Gmail** | ❌ Pendiente | No hay integración con Gmail API para mover emails a carpeta específica |

**Resumen**: Las acciones a nivel SMTP están completas (block, quarantine, warn+forward). Faltan las acciones post-delivery dentro de Gmail (etiquetar, mover) y la entrega real de alertas.

---

### 1.4 Dashboard y Frontend

| Componente | Estado | Detalle |
|---|---|---|
| KPI cards (total, threats, blocked, avg time) | ✅ Completo | 4 cards con `StatsCard.vue`, font-mono, hover glow, badges |
| Trend chart (últimos 30 días) | ✅ Completo | Line chart diario con Chart.js |
| Risk distribution (pie + barras) | ✅ Completo | Toggle doughnut/barras horizontales con animación de entrada, barra apilada con leyenda |
| Threat categories breakdown | ✅ Completo | Componente dedicado `ThreatCategories.vue` |
| Pipeline health metrics | ✅ Completo | avg_duration_ms, success_rate, stage_avg_ms por etapa |
| Recent critical cases | ✅ Completo | Últimos 10 casos con badges de riesgo y acción |
| Active alerts panel | ✅ Completo | Últimos 10 alert events, glow naranja en hover |
| Top Senders | ✅ Completo | `TopSenders.vue` — Top 10 remitentes, avg score, click filtra dashboard |
| Verdict Timeline | ✅ Completo | `VerdictTimeline.vue` — Line chart blocked/quarantined/warned/allowed en el tiempo |
| Score Distribution | ✅ Completo | `ScoreDistribution.vue` — Histograma de distribución de scores por buckets |
| Global Filters Bar | ✅ Completo | `GlobalFiltersBar.vue` — Presets (today/week/month), rango custom, filtro por sender |
| Design System implementado | ✅ Completo | Dual font (JetBrains Mono + Inter), variables CSS, glow effects, hover animations |
| Sidebar rediseñada | ✅ Completo | Font-mono, logo con glow pulsante, active state con borde cyan, estética cybersecurity |
| Topbar rediseñada | ✅ Completo | Breadcrumbs mono, search box, user chip con borde cyan, avatar glow |
| UX global | ✅ Completo | Custom scrollbar cyan, selection color, focus outlines, font smoothing |
| Formateo de fechas | ✅ Completo | Formato `dd/mm/yyyy HH:mm` en toda la app |
| Cases view completa | ✅ Completo | KPI cards, sección "Needs Action", filtros (search, risk, action, status, fecha), paginación, export CSV |
| Case Detail con 3 tabs | ✅ Completo | Overview (KPIs, auth, risk bar), Email Content (headers, body, URLs), Pipeline Results (stages expandibles) |
| Notifications view | ✅ Completo | Lista con unread count, mark as read, tipos y severidad |
| **Reports UI** | ❌ Pendiente | Backend tiene CSV/PDF export implementado, pero frontend es "Coming Soon" stub |
| **FP Review UI** | ❌ Pendiente | Frontend es "Coming Soon" stub. Backend `fp_review_service.py` existe |

**Resumen**: Dashboard completo con 10 componentes, filtros globales, Design System cybersecurity implementado. Frontend funcional para Dashboard, Cases, Case Detail y Notifications. Falta UI de Reports y FP Review.

---

### 1.5 Definición y documentación del plan de datos y métricas de evaluación

| Componente | Estado | Detalle |
|---|---|---|
| Modelo de datos documentado | ✅ Completo | `docs/modelo-datos.md` — 494 líneas, 14 tablas, constraints, índices, proyecciones |
| Diagnóstico de implementación | ✅ Completo | `docs/review-diagnostico-completo.md` — Auditoría completa |
| **Métricas de evaluación del modelo ML** | ❌ Pendiente | No hay documento definiendo: accuracy, precision, recall, F1 targets; confusion matrix thresholds; ROC/AUC expectations |
| **Plan de datos (recolección, labeling, ground truth)** | ❌ Pendiente | No hay documento sobre: fuentes de datos, estrategia de labeling, volumen esperado, proceso de ground truth |
| **Benchmark de heurísticas** | ❌ Pendiente | No hay evaluación formal del motor heurístico contra un dataset etiquetado |

**Resumen**: Documentación técnica del modelo de datos existe. Falta documentación académica/científica sobre métricas de evaluación y plan de datos.

---

## 2. Resumen Ejecutivo

### Lo que YA está hecho para v0.2

1. **Pipeline completo de 3 etapas** funcionando (heurísticas → ML placeholder → LLM explainer)
2. **SMTP Gateway** recibiendo, procesando y reenviando emails
3. **Motor heurístico robusto** con 4 sub-engines y 12+ tipos de evidencia
4. **Sistema de quarantine** completo con release/keep/delete
5. **Dashboard completo** con 10 componentes: KPIs, ThreatChart, RiskDistribution (toggle barras/pie), VerdictTimeline, ScoreDistribution, ThreatCategories, TopSenders, RecentCases, PipelineHealth, ActiveAlerts
6. **GlobalFiltersBar** con presets de fecha (today/week/month) y filtro por sender
7. **Design System cybersecurity** implementado: dual font (JetBrains Mono + Inter), glow effects, hover animations, custom scrollbar cyan, focus outlines
8. **Sidebar y Topbar** rediseñados con estética dark/futurista: logo con glow pulsante, nav items mono, active state con borde cyan, breadcrumbs mono, user chip con glow
9. **Cases view completa** con KPI cards, sección "Needs Action", filtros avanzados (search, risk, action, status, fecha), paginación, export CSV
10. **Case Detail rediseñado** con 3 tabs (Overview, Email Content, Pipeline Results), notas, modal de acciones
11. **Case IDs incrementales** (#1, #2, #3...)
12. **Alert rules engine** evaluando condiciones con CRUD completo
13. **Whitelist/Blacklist** integrada con el pipeline
14. **Infraestructura ML** completa (training code, inference code, MLflow)
15. **Notifications view** funcional con unread count, mark as read, tipos y severidad
16. **Formateo de fechas** mejorado (dd/mm/yyyy HH:mm)

### Lo que FALTA para v0.2

| # | Tarea | Prioridad | Complejidad | Área |
|---|---|---|---|---|
| 1 | Conseguir dataset de phishing y entrenar DistilBERT | Critica | Alta | ML |
| 2 | Configurar Google Workspace routing rules para recibir emails reales | Critica | Media | Infra/Google |
| 3 | Documentar plan de datos y métricas de evaluación | Critica | Media | Docs/Académico |
| 4 | Implementar UI de Reports (CSV/PDF export) | Alta | Baja | Frontend |
| 5 | Implementar UI de FP Review | Alta | Media | Frontend |
| 6 | Integrar Gmail Labels API para etiquetar emails | Alta | Alta | Backend/Google |
| 7 | Implementar entrega real de alertas (email/Slack webhook) | Alta | Media | Backend |
| 8 | Evaluar heurísticas contra dataset etiquetado (benchmark) | Alta | Media | ML/Testing |
| 9 | Tests reales (pipeline, API, integration) — cobertura actual 0% (solo stubs) | Media | Alta | Testing |

---

## Mejoras implementadas (sesión actual)

### Design System & Estética
- **Dual font system**: JetBrains Mono (títulos, valores, badges, buttons, nav, breadcrumbs) + Inter (body, labels, inputs)
- **Variables CSS actualizadas**: `--font-mono`, `--bg-inset`, `--bg-sidebar`, `--border-subtle`, `--glow-cyan`, `--glow-cyan-strong`
- **Colores de texto aclarados** para mejor legibilidad: `--text-primary: #F1F5F9`, `--text-secondary: #A0ABBE`, `--text-muted: #6B7A8D`
- **Sidebar background diferenciado**: `--bg-sidebar: #0A1120` (más claro que el contenido)
- **Bordes más visibles**: `--border-color: #1E2A3A`

### Sidebar
- Logo text: font-mono, uppercase, letter-spacing 1.5px
- Logo icon: animación pulse-glow cyan (3s infinite)
- Nav items: font-mono 13px, color muted → hover primary → active cyan con `box-shadow: inset 3px 0 0`
- Nav icons: opacity 0.7, active con drop-shadow glow
- User name: font-mono 12px, weight 600
- User role: font-mono, uppercase, cyan, letter-spacing 0.8px
- Footer: background overlay oscuro

### Topbar
- Breadcrumbs: font-mono 12px, hover cambia a cyan
- Search box: bg-inset, hover border glow cyan
- Notification icon: border on hover, cyan glow
- User chip: bordered, cyan glow on hover, avatar con cyan ring
- User name: font-mono

### Dashboard Cards
- Hover glow en TODAS las cards (cyan para normales, naranja para alerts)
- StatsCard: label 11px + letterSpacing, value font-mono, icon opacity 0.35, badge mono
- Todos los títulos de card: font-mono

### RiskDistribution
- Toggle barras/pie con iconos Material (bar_chart/pie_chart)
- Vista barras: horizontal progress bars con label, valor y porcentaje (ej: "3 (33%)")
- Barra apilada "Overall Distribution" con leyenda de colores
- Animación de entrada (barras crecen de 0% al valor real)

### UX Global
- Custom scrollbar: thin 6px, cyan-tinted
- Selection color: cyan tint
- Focus outlines: cyan
- Font smoothing: antialiased

### Cases View
- KPI values: font-mono
- KPI labels: letter-spacing 0.5px
- Headers: font-mono
- Badges: font-mono, border-radius-xs
- Formateo de fechas: dd/mm/yyyy HH:mm

### Shared Components (components.css)
- Badges (pill, count): font-mono
- Buttons (primary, outline, success): font-mono, padding ajustado
- Table headers: font-mono, letter-spacing 0.5px, bg-inset
- Filter inputs: bg-inset, border-radius
- Page buttons: font-mono
- Table card: hover glow

---

## 3. Detalle de Tareas Pendientes

### TAREA 1: Dataset y entrenamiento de DistilBERT (Critica)

**Estado actual**: `ml/models/distilbert-guardia/` vacío, `ml/data/` vacío. Training code listo.

**Pasos**:
1. Obtener dataset de phishing emails (opciones: Nazario phishing corpus, CEAS, Nigerian fraud corpus, o dataset propio)
2. Preparar CSVs con columnas `text` (subject + body) y `label` (0=legit, 1=phishing)
3. Ejecutar `python -m ml.src.preprocess` para split estratificado
4. Ejecutar `python -m ml.src.train` para fine-tune DistilBERT (3 epochs, batch 8)
5. Verificar métricas en MLflow (http://localhost:5000)
6. Copiar modelo a `ml/models/distilbert-guardia/` o configurar path en `.env`
7. Verificar que el pipeline use 40% heurísticas + 60% ML (en vez del fallback 100% heurísticas)

**Archivos clave**: `ml/src/train.py`, `ml/src/preprocess.py`, `ml/src/config.py`

---

### TAREA 2: Configurar Google Workspace routing (Critica)

**Estado actual**: Gateway escucha en :2525, relay configurado hacia aspmx.l.google.com. Solo funciona con simulador.

**Pasos**:
1. Configurar dominio de pruebas en Google Workspace Admin
2. Crear inbound gateway rule: rutear copia de emails entrantes al IP:2525 del servidor Guard-IA
3. Configurar TLS certificates para el gateway (`smtp_tls_cert`, `smtp_tls_key` en config)
4. Testear con email real: enviar email al dominio de pruebas, verificar que pasa por Guard-IA
5. Verificar que el relay forward funciona de vuelta a Gmail

**Archivos clave**: `app/config.py` (líneas 18-29), `app/gateway/server.py`

---

### TAREA 3: Documentar plan de datos y métricas (Critica)

**Estado actual**: Existe `docs/modelo-datos.md` (schema) pero no hay documentación de métricas ML.

**Documento a crear** (`docs/plan-datos-metricas.md`):
- Fuentes de datos (datasets públicos + datos simulados + datos reales futuros)
- Estrategia de labeling (manual review, ground truth definition)
- Volumen esperado por fase (simulación → piloto → producción)
- Métricas target: Accuracy >= 95%, Recall >= 99% (minimizar falsos negativos), Precision >= 90%
- Evaluation framework: confusion matrix, ROC curve, F1 score, por categoría de amenaza
- Plan de re-entrenamiento (frecuencia, triggers, data drift detection)

---

### TAREA 4: UI de Reports (Alta)

**Estado actual**: Backend `report_service.py` genera CSV/PDF. Frontend es stub "Coming Soon".

**Pasos**:
1. Crear formulario con filtros (fecha, verdict, risk_level, threat_category)
2. Botones "Export CSV" y "Export PDF" que llamen a los endpoints existentes
3. Download del archivo generado

**Archivos**: `frontend/src/views/ReportsView.vue`, `backend/app/api/v1/reports.py`

---

### TAREA 5: UI de FP Review (Alta)

**Estado actual**: Backend `fp_review_service.py` existe. Frontend es stub "Coming Soon".

**Pasos**:
1. Listar casos marcados como false positive pendientes de revisión
2. Interfaz para revisar, confirmar o rechazar cada FP
3. Actualizar estado del caso y re-entrenar si aplica

**Archivos**: `frontend/src/views/FPReviewView.vue`, `backend/app/services/fp_review_service.py`

---

### TAREA 6: Gmail Labels API (Alta)

**Estado actual**: No existe integración con Gmail API. Solo SMTP relay.

**Pasos**:
1. Crear service account en Google Cloud Console con Gmail API scope
2. Implementar `GmailClient` en backend que use google-auth + google-api-python-client
3. Crear labels en Gmail: "Guard-IA: Suspicious", "Guard-IA: Phishing", "Guard-IA: Safe"
4. Después del pipeline, si verdict=WARNED, aplicar label "Suspicious" al email en Gmail
5. Configurar en `policy_service.py` o como nueva acción automática

---

### TAREA 7: Entrega de alertas (Alta)

**Estado actual**: `alert_service.py` crea AlertEvents con `delivery_status=PENDING` pero no los envía.

**Pasos**:
1. Implementar `AlertDeliveryWorker` (async background task)
2. Para channel=EMAIL: enviar via SMTP (aiosmtplib) al CISO
3. Para channel=SLACK: POST a Slack webhook URL
4. Actualizar `delivery_status` a DELIVERED/FAILED
5. Integrar con el pipeline (llamar `evaluate_and_fire` después de cada análisis)

---

### TAREA 8: Benchmark de heurísticas (Alta)

**Estado actual**: Motor heurístico funciona pero no hay evaluación formal.

**Pasos**:
1. Usar el mismo dataset de la Tarea 1 como ground truth
2. Ejecutar todas las heurísticas contra el dataset
3. Calcular precision/recall/F1 del motor heurístico solo
4. Documentar fortalezas/debilidades (ej: bueno en auth checks, débil en BEC sin typosquatting)
5. Usar como baseline para comparar con el modelo ML

---

### TAREA 9: Tests reales (Media)

**Estado actual**: 12 archivos de test, todos son stubs con `pass` o `# TODO`. 0% de cobertura real.

**Archivos existentes** (todos vacíos):
- Unit: `test_heuristics.py`, `test_llm_explainer.py`, `test_ml_classifier.py`, `test_orchestrator.py`, `test_security.py`
- Integration: `test_email_ingestion.py`, `test_pipeline_flow.py`, `test_quarantine_flow.py`
- API: `test_dashboard.py`, `test_auth.py`, `test_cases.py`, `test_emails.py`

**Pasos**:
1. Implementar unit tests para heurísticas (mayor cobertura, lógica crítica)
2. Implementar API tests para endpoints principales
3. Implementar integration tests para el pipeline completo
4. Target: >= 50% cobertura para v0.2

---

## 4. Progreso General v0.2

```
Integración Google Workspace:  ██████████░░░░░ 70%  (infra lista, falta ruteo real)
Modelo ML clasificación:       ████░░░░░░░░░░░ 30%  (code listo, falta dataset+training)
Acciones automáticas:          ████████░░░░░░░ 55%  (SMTP actions OK, falta Gmail API + alertas)
Dashboard + Frontend:          ██████████████░ 95%  (completo, falta Reports UI + FP Review UI)
Documentación datos/métricas:  ██████░░░░░░░░░ 40%  (schema docs OK, falta plan ML)
Testing:                       █░░░░░░░░░░░░░░  5%  (stubs creados, 0% implementación)
```

**Progreso estimado total v0.2: ~60%**
