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
| **Ruteo real desde Google Workspace** | 🔄 Diseño | Gateway preparado para recibir. Se implementará filtro por usuario en el handler para activar solo para `nicolas.sogliano@strike.sh` (ver análisis en Tarea 2) |

**Resumen**: La infraestructura técnica está 100% lista. La conexión con Google Workspace se posterga estratégicamente por la limitación de que el routing rule aplica a toda la organización. Se diseñó un filtro por usuario a nivel código para mitigar el riesgo.

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
| **Modelo entrenado (weights)** | 🔄 En proceso | Otro miembro del equipo se encarga del entrenamiento. Esperando integración al proyecto |
| **Dataset de entrenamiento** | 🔄 En proceso | Dataset conseguido por el equipo de ML. Pendiente de integración |
| **Ponderación ML+Heurísticas** | ✅ Listo (inactivo) | Configurado: 40% heurísticas + 60% ML. Actualmente cae a 100% heurísticas porque el modelo no existe |
| LLM Explainer (Claude + GPT fallback) | ✅ Completo | `llm_explainer.py` — Solo explica, no decide. Funciona pero requiere API keys configuradas |

**Resumen**: El framework completo de ML está implementado end-to-end (training → inference → pipeline integration). Un compañero del equipo tiene el dataset y se encarga del entrenamiento. Pendiente de integración cuando el pipeline esté estabilizado.

---

### 1.3 Acciones automáticas iniciales

| Componente | Estado | Detalle |
|---|---|---|
| Quarantine automática (score ≥ 0.8) | ✅ Completo | Gateway almacena raw email en disco, case marcado como QUARANTINED |
| Warning headers (0.3 ≤ score < 0.6) | ✅ Completo | Relay inyecta `X-Guard-IA-Warning: true` al forward a Google |
| Block/Reject (score ≥ 0.8) | ✅ Completo | Gateway retorna SMTP 550 reject |
| Quarantine management (release/keep/delete) | ✅ Completo | `quarantine_service.py` — CISO puede liberar, mantener o eliminar emails |
| Alert rules engine | ✅ Completo | `alert_service.py` — Reglas por score, verdict, risk_level, threat_category. CRUD completo + evaluación |
| **Entrega de alertas Slack** | 🔧 En implementación | Se implementará Slack webhook delivery para AlertEvents pendientes |
| ~~Etiquetado en Gmail (labels)~~ | ❌ Descartado | Se decidió no implementar. Innecesario para el scope de la tesis |
| ~~Mover a carpeta en Gmail~~ | ❌ Descartado | Descartado junto con Gmail Labels API |

**Resumen**: Las acciones a nivel SMTP están completas (block, quarantine, warn+forward). Se está implementando entrega real de alertas vía Slack. Gmail Labels API descartado del scope.

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
| Reports UI | ⏸️ Postergado | Backend tiene CSV/PDF export implementado. Frontend se implementará en fase posterior |
| FP Review UI | ⏸️ Postergado | Backend `fp_review_service.py` existe. Frontend se implementará en fase posterior |

**Resumen**: Dashboard completo con 10 componentes, filtros globales, Design System cybersecurity implementado. Frontend funcional para Dashboard, Cases, Case Detail y Notifications. Reports y FP Review postergados.

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

### 1.6 Testing

| Componente | Estado | Detalle |
|---|---|---|
| Unit tests — Heuristics engine | ✅ Completo | `test_heuristics.py` — 30 tests: 4 sub-engines completos, Levenshtein, composite score, boundary cases |
| Unit tests — Email parser | ✅ Completo | `test_parser.py` — 19 tests: RFC 5322 parsing, multipart, URLs, auth results, attachments, dates |
| Unit tests — Orchestrator | ✅ Completo | `test_orchestrator.py` — 30 tests: scoring, thresholds, verdicts, risk levels, threat categories, full analyze flow, LLM failure, auto-quarantine |
| Unit tests — Alert service | ✅ Completo | `test_alert_service.py` — 13 tests: rule matching AND logic, evaluate_and_fire, channels |
| Unit tests — ML classifier | ✅ Completo | `test_ml_classifier.py` — 8 tests: degraded mode, singleton, happy path mock, _load_model |
| Unit tests — LLM explainer | ✅ Completo | `test_llm_explainer.py` — 9 tests: Claude primary, OpenAI fallback, both fail, no keys, _build_user_prompt, API mocks |
| Unit tests — JWT security | ✅ Completo | `test_security.py` — 4 tests: valid RS256, expired, invalid signature, garbage token |
| Coverage config | ✅ Completo | `pyproject.toml` con pytest-cov, HTML report en `htmlcov/`, `fail_under=90%` |
| **Integration tests** | ❌ Pendiente | Stubs existentes: `test_email_ingestion.py`, `test_pipeline_flow.py`, `test_quarantine_flow.py` |
| **API tests** | ❌ Pendiente | Stubs existentes: `test_dashboard.py`, `test_auth.py`, `test_cases.py`, `test_emails.py` |

**Métricas actuales**:
- **113 unit tests**, todos pasando
- **96.47% coverage** sobre lógica de negocio (pipeline, heuristics, parser, orchestrator, alert matching, ML classifier, LLM explainer, JWT)
- **Ejecución**: 4.24s
- **CI gate**: `fail_under = 90%`

**Resumen**: Unit tests con cobertura sólida sobre toda la lógica de negocio crítica. Faltan integration tests y API tests (requieren PostgreSQL).

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
17. **113 unit tests** con 96.47% de coverage sobre lógica de negocio, CI gate a 90%

### Lo que FALTA para v0.2

| # | Tarea | Prioridad | Complejidad | Estado | Área |
|---|---|---|---|---|---|
| 1 | Integrar modelo DistilBERT entrenado por el equipo de ML | Critica | Media | Esperando al compañero | ML |
| 2 | Preparar gateway con filtro por usuario para Google Workspace | Critica | Media | Diseño listo, ver análisis | Infra/Gateway |
| 3 | Documentar plan de datos y métricas de evaluación | Critica | Media | Pendiente | Docs/Académico |
| 4 | Implementar entrega real de alertas (Slack webhook) | Alta | Media | En implementación | Backend |
| 5 | Evaluar heurísticas contra dataset etiquetado (benchmark) | Alta | Media | Pendiente (requiere dataset) | ML/Testing |
| 6 | Integration tests y API tests | Media | Alta | Pendiente | Testing |

**Tareas descartadas del scope v0.2:**
- ~~Gmail Labels API~~ — Innecesario
- ~~UI de Reports~~ — Postergado a fase posterior
- ~~UI de FP Review~~ — Postergado a fase posterior

---

## Mejoras implementadas (sesiones anteriores)

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

### Testing (sesión actual)
- **113 unit tests** implementados desde cero (antes: 0% cobertura, solo stubs)
- **8 archivos de test**: test_heuristics (30), test_parser (19), test_orchestrator (30), test_alert_service (13), test_ml_classifier (8), test_llm_explainer (9), test_security (4)
- **conftest.py** con fixtures compartidos: mock_db, clean_email_data, phishing_email_data, make_mock_policies
- **96.47% coverage** sobre lógica de negocio relevante
- **CI gate**: `fail_under = 90%` en pyproject.toml
- **HTML report**: `htmlcov/index.html` para documentación visual
- **pytest-cov** configurado con exclusiones inteligentes (CRUD boilerplate, models, schemas, API endpoints excluidos del scope de unit tests)

---

## 3. Detalle de Tareas Pendientes

### TAREA 1: Integrar modelo DistilBERT del equipo de ML (Critica)

**Estado actual**: Otro miembro del equipo se encargó del entrenamiento del modelo. Está esperando que el pipeline esté estabilizado para integrar los weights.

**Pasos para la integración**:
1. Recibir los weights y tokenizer del compañero
2. Copiar a `ml/models/distilbert-guardia/` o configurar path en `.env`
3. Verificar que `ml_classifier.py` carga el modelo correctamente (singleton, lazy load)
4. Testear que el pipeline usa 40% heurísticas + 60% ML (en vez del fallback 100% heurísticas)
5. Verificar métricas de inferencia (latencia, score distribution)

**Archivos clave**: `app/services/pipeline/ml_classifier.py`, `ml/models/distilbert-guardia/`

---

### TAREA 2: Preparar gateway con filtro por usuario para Google Workspace (Critica)

**Estado actual**: Gateway escucha en :2525, relay configurado hacia aspmx.l.google.com. Solo funciona con simulador.

**Problema**: Google Workspace Admin Console solo permite configurar inbound gateway routing rules a nivel de toda la organización. No hay forma nativa de activarlo solo para un usuario.

**Solución propuesta**: Implementar filtro por usuario a nivel código en el gateway handler.

**Diseño**:
- Nueva config: `GUARDIA_ACTIVE_USERS` (env var, lista de emails)
- En `handle_DATA` del `GuardIAHandler`, antes de correr el pipeline:
  - Verificar si ALGUNO de los recipients está en `GUARDIA_ACTIVE_USERS`
  - Si NO → bypass pipeline, forward inmediato a Google (retornar 250 OK + relay directo)
  - Si SI → ejecutar pipeline normalmente
- Para la tesis: `GUARDIA_ACTIVE_USERS=nicolas.sogliano@strike.sh`

**Análisis de viabilidad y riesgos**:

| Aspecto | Evaluación |
|---|---|
| **Viabilidad** | ✅ Alta. El handler ya tiene la lista de recipients en `envelope.rcpt_tos`. Agregar un check es trivial (~10 líneas) |
| **Rendimiento** | ✅ Sin impacto. El check es O(1) con un set. Los emails bypass no tocan DB ni pipeline |
| **Fail-open** | ✅ Ya implementado. Si el gateway crashea, forward sin análisis. Si un usuario no está en la lista, forward sin análisis. Mismo comportamiento |
| **Riesgo: email delay** | ⚠️ Bajo. El pipeline tarda ~3s (heurísticas ~5ms + LLM ~2-3s). Para usuarios bypass: 0ms extra. Para el usuario activo: latencia ya aceptada |
| **Riesgo: email loss** | ✅ Mínimo. Arquitectura fail-open: si algo falla, el email se entrega. Solo se bloquean emails con score ≥ 0.8 (blocked/quarantined), y eso es intencional |
| **Riesgo: toda la org pasa por el gateway** | ⚠️ Principal riesgo. Todos los emails de strike.sh pasarían por el servidor Guard-IA, aunque solo se analice uno. Si el servidor se cae, Gmail tiene retry pero podría haber delay temporal para todos |
| **Mitigación: health check** | Se puede agregar un health endpoint y configurar Google Workspace para remove gateway si falla (o tener un servidor de fallback) |
| **Riesgo: privacidad** | ⚠️ Medio. Técnicamente el gateway "ve" todos los emails aunque no los procese. No persiste nada para usuarios bypass (forward directo). Documentar en la tesis que es un entorno controlado de pruebas |
| **Alternativa: BCC rule** | En vez de inbound gateway, configurar una regla de routing que haga BCC a una dirección que reciba Guard-IA. Esto es post-delivery (no pre-delivery) pero elimina el riesgo de bloquear emails de otros usuarios. No cumple el objetivo de pre-delivery pero es más seguro para pruebas |

**Recomendación**: Implementar el filtro por usuario (es simple y el diseño fail-open mitiga los riesgos principales). Para la tesis, documentar los riesgos y la decisión.

**Pasos**:
1. Agregar `active_users: str = ""` en `config.py` con property `active_users_list`
2. En `handle_DATA` de `handler.py`, agregar check de recipients contra active_users
3. Si ningún recipient es active → `self.relay.forward()` directo, retornar 250 OK
4. Si algún recipient es active → ejecutar pipeline normal
5. Testear con simulador: email a `nicolas.sogliano@strike.sh` → pipeline; email a `otro@strike.sh` → bypass
6. Configurar Google Workspace: inbound gateway rule hacia IP del servidor

**Archivos clave**: `app/config.py`, `app/gateway/handler.py`

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

### TAREA 4: Entrega real de alertas — Slack webhook (Alta)

**Estado actual**: `alert_service.py` crea AlertEvents con `delivery_status=PENDING` pero no los envía.

**Pasos**:
1. Crear canal de test en Slack de Strike Security
2. Crear Slack App y obtener webhook URL
3. Implementar `SlackDeliveryService` que haga POST al webhook
4. Formato del mensaje: severity badge, rule name, case link, score, verdict
5. Actualizar `delivery_status` a DELIVERED/FAILED
6. Integrar: después de `evaluate_and_fire()`, procesar AlertEvents pendientes

**Cómo obtener los tokens de Slack**:
1. Ir a https://api.slack.com/apps → Create New App → From Scratch
2. Nombre: "Guard-IA Alerts", workspace: Strike Security
3. En "Incoming Webhooks" → Activate → Add New Webhook to Workspace
4. Seleccionar el canal de test → Copiar la Webhook URL (formato: `https://hooks.slack.com/services/T.../B.../xxx`)
5. Esa URL es todo lo que se necesita. No hace falta Bot Token ni OAuth para webhooks

**Archivos clave**: Nuevo `app/services/slack_service.py`, `app/services/alert_service.py`

---

### TAREA 5: Benchmark de heurísticas (Alta)

**Estado actual**: Motor heurístico funciona y tiene 96%+ coverage en tests, pero no hay evaluación formal contra un dataset etiquetado.

**Requiere**: Dataset de la Tarea 1 (del compañero de ML).

**Pasos**:
1. Usar el mismo dataset como ground truth
2. Ejecutar todas las heurísticas contra el dataset
3. Calcular precision/recall/F1 del motor heurístico solo
4. Documentar fortalezas/debilidades (ej: bueno en auth checks, débil en BEC sin typosquatting)
5. Usar como baseline para comparar con el modelo ML

---

### TAREA 6: Integration tests y API tests (Media)

**Estado actual**: 113 unit tests con 96.47% coverage. Stubs de integration y API tests existen pero no implementados.

**Stubs existentes**:
- Integration: `test_email_ingestion.py`, `test_pipeline_flow.py`, `test_quarantine_flow.py`
- API: `test_dashboard.py`, `test_auth.py`, `test_cases.py`, `test_emails.py`

**Requiere**: PostgreSQL corriendo para integration/API tests.

**Pasos**:
1. Configurar test database (fixture que crea/destruye schema por sesión)
2. Implementar integration tests del pipeline completo (email in → case out)
3. Implementar API tests para endpoints principales con httpx AsyncClient

---

## 4. Progreso General v0.2

```
Integración Google Workspace:  ████████░░░░░░░ 55%  (infra lista, diseño de filtro por usuario listo, falta implementar + configurar)
Modelo ML clasificación:       ████░░░░░░░░░░░ 30%  (code listo, modelo en manos del equipo ML)
Acciones automáticas:          █████████░░░░░░ 65%  (SMTP actions OK, alertas Slack en implementación. Gmail Labels descartado)
Dashboard + Frontend:          ██████████████░ 95%  (completo. Reports y FP Review postergados)
Documentación datos/métricas:  ██████░░░░░░░░░ 40%  (schema docs OK, falta plan ML)
Testing:                       ██████████░░░░░ 70%  (113 unit tests, 96.47% coverage. Faltan integration + API tests)
```

**Progreso estimado total v0.2: ~65%**
