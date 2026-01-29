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
| Alert rules engine | ✅ Completo | `alert_service.py` — Reglas por score, verdict, risk_level, threat_category |
| **Entrega de alertas (email/Slack)** | ❌ Pendiente | El engine evalúa reglas y persiste AlertEvents, pero no hay worker que envíe emails/Slack |
| **Etiquetado en Gmail (labels)** | ❌ Pendiente | No hay integración con Gmail Labels API para marcar emails como sospechosos |
| **Mover a carpeta en Gmail** | ❌ Pendiente | No hay integración con Gmail API para mover emails a carpeta específica |

**Resumen**: Las acciones a nivel SMTP están completas (block, quarantine, warn+forward). Faltan las acciones post-delivery dentro de Gmail (etiquetar, mover) y la entrega real de alertas.

---

### 1.4 Dashboard v0

| Componente | Estado | Detalle |
|---|---|---|
| KPI cards (total, threats, blocked, avg time) | ✅ Completo | 4 cards en `DashboardView.vue` |
| Trend chart (últimos 30 días) | ✅ Completo | Bar chart diario con Chart.js |
| Risk distribution (pie chart) | ✅ Completo | Doughnut chart por risk level |
| Threat categories breakdown | ✅ Completo | Backend retorna conteo por categoría |
| Pipeline health metrics | ✅ Completo | avg_duration_ms, success_rate, stage_avg_ms |
| Recent critical cases | ✅ Completo | Últimos 10 casos |
| Active alerts panel | ✅ Completo | Últimos 10 alert events |
| **Vista por remitente** | ❌ Pendiente | No hay agregación "top senders" ni "threats by sender" |
| **Vista por día con granularidad** | ⚠️ Parcial | Existe trend diario 30 días, pero no hay filtro de rango de fechas ni desglose por verdict/hora |
| **Reports UI** | ❌ Pendiente | Backend tiene CSV/PDF export implementado, pero frontend es "Coming Soon" stub |

**Resumen**: Dashboard funcional con métricas clave. Falta agregación por remitente y la UI de reportes.

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
5. **Dashboard funcional** con KPIs, charts, pipeline health
6. **Case Detail rediseñado** con 3 tabs (Overview, Email Content, Pipeline Results)
7. **Case IDs incrementales** (#1, #2, #3...)
8. **Alert rules engine** evaluando condiciones
9. **Whitelist/Blacklist** integrada con el pipeline
10. **Infraestructura ML** completa (training code, inference code, MLflow)

### Lo que FALTA para v0.2

| # | Tarea | Prioridad | Complejidad | Área |
|---|---|---|---|---|
| 1 | Conseguir dataset de phishing y entrenar DistilBERT | 🔴 Crítica | Alta | ML |
| 2 | Configurar Google Workspace routing rules para recibir emails reales | 🔴 Crítica | Media | Infra/Google |
| 3 | Documentar plan de datos y métricas de evaluación | 🔴 Crítica | Media | Docs/Académico |
| 4 | Agregar vista "por remitente" al dashboard | 🟡 Alta | Baja | Full-stack |
| 5 | Implementar UI de Reports (CSV/PDF export) | 🟡 Alta | Baja | Frontend |
| 6 | Integrar Gmail Labels API para etiquetar emails | 🟡 Alta | Alta | Backend/Google |
| 7 | Implementar entrega real de alertas (email/Slack webhook) | 🟡 Alta | Media | Backend |
| 8 | Evaluar heurísticas contra dataset etiquetado (benchmark) | 🟡 Alta | Media | ML/Testing |
| 9 | Agregar filtro de rango de fechas al dashboard | 🟢 Media | Baja | Full-stack |
| 10 | Tests reales (pipeline, API, integration) — cobertura actual ~15% | 🟢 Media | Alta | Testing |

---


## Mejoras mias:

Sobre los Cases:

1. En la vista de Overview, me gustaría:
    - El score de ariba a la derecha me gustaría que tenga un circulo al rededor que muestre la completitud tambien, de 0 a 100 que sea, y que tenga color según el riesgo.
    - En Email Information tenemos threat category. Buscaría alguna manera de tener definidas unas categorías y mostrarlo tipo badge ahí. Que cuando pase el mouse arriba se muestre la descripción de la category.
    - El AI Analysis Summary me gusta que esté ahí. No mostraría lo de Provider ni Model. 
    - Que el Authentication Status explique en algun lado que es lo que se esta mostrando, puede haber un tooltip o algo así para obtener más detalle. Aparece SPF SOFTFAIL, DKIM FAIL, DMARC FAIL y no tengo idea que es eso ni que es lo que estoy viendo ni nada.
    - El Risk Score breakdown lo veo muy bien.
    - La parte de Actions está bastante fea estéticamente, y dice Resolve case solamente. Te consulto, cual es la idea de esta parte? Que el usuario (CISO de Strike) pueda tomar accion sobre un caso y modificar el estado, o que? Veo que en la tabla de cases hay score, risk, action y status. Que vendria a ser el status? Quiero comprender un poco más esto de las actions sobre los cases. Lo de False Positive Review no lo entendí tampoco. Comentame tu enfoque y entendamoslo juntos.

1. http://localhost:3000/cases/0e36ed6c-df2e-43e3-a61d-45e9a8564deb: hacer que cada elemento (email headers, email body, extracted urls), todo todo, sea colapsable, como el email headers que podes ocultarlo y mostrarlo, pero con todo. Además, queiro que en las Notes dentro de cada case detail se muestre el nombre del user que lo hace, en lugar de el ID del autor. También me gustaría que cada comentario tenga un icono para editarlo y modificar la nota realizada.

2. http://localhost:3000/cases/ea5567e2-1173-4246-a7e7-9aadcc3eedc1




## 3. Detalle de Tareas Pendientes

### TAREA 1: Dataset y entrenamiento de DistilBERT (🔴 Crítica)

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

### TAREA 2: Configurar Google Workspace routing (🔴 Crítica)

**Estado actual**: Gateway escucha en :2525, relay configurado hacia aspmx.l.google.com. Solo funciona con simulador.

**Pasos**:
1. Configurar dominio de pruebas en Google Workspace Admin
2. Crear inbound gateway rule: rutear copia de emails entrantes al IP:2525 del servidor Guard-IA
3. Configurar TLS certificates para el gateway (`smtp_tls_cert`, `smtp_tls_key` en config)
4. Testear con email real: enviar email al dominio de pruebas, verificar que pasa por Guard-IA
5. Verificar que el relay forward funciona de vuelta a Gmail

**Archivos clave**: `app/config.py` (líneas 18-29), `app/gateway/server.py`

---

### TAREA 3: Documentar plan de datos y métricas (🔴 Crítica)

**Estado actual**: Existe `docs/modelo-datos.md` (schema) pero no hay documentación de métricas ML.

**Documento a crear** (`docs/plan-datos-metricas.md`):
- Fuentes de datos (datasets públicos + datos simulados + datos reales futuros)
- Estrategia de labeling (manual review, ground truth definition)
- Volumen esperado por fase (simulación → piloto → producción)
- Métricas target: Accuracy ≥ 95%, Recall ≥ 99% (minimizar falsos negativos), Precision ≥ 90%
- Evaluation framework: confusion matrix, ROC curve, F1 score, por categoría de amenaza
- Plan de re-entrenamiento (frecuencia, triggers, data drift detection)

---

### TAREA 4: Vista por remitente en dashboard (🟡 Alta)

**Estado actual**: Dashboard tiene trend diario y risk distribution, pero no agrega por sender.

**Pasos**:
1. Backend: agregar `_get_top_senders()` a `dashboard_service.py` — JOIN cases + emails, GROUP BY sender_email, ORDER BY count DESC, LIMIT 10
2. Schema: agregar `top_senders: list[TopSenderItem]` a `DashboardResponse`
3. Frontend: agregar componente de tabla "Top Senders" en `DashboardView.vue`

---

### TAREA 5: UI de Reports (🟡 Alta)

**Estado actual**: Backend `report_service.py` genera CSV/PDF. Frontend es stub "Coming Soon".

**Pasos**:
1. Crear formulario con filtros (fecha, verdict, risk_level, threat_category)
2. Botones "Export CSV" y "Export PDF" que llamen a los endpoints existentes
3. Download del archivo generado

**Archivos**: `frontend/src/views/ReportsView.vue`, `backend/app/api/v1/reports.py`

---

### TAREA 6: Gmail Labels API (🟡 Alta)

**Estado actual**: No existe integración con Gmail API.

**Pasos**:
1. Crear service account en Google Cloud Console con Gmail API scope
2. Implementar `GmailClient` en backend que use google-auth + google-api-python-client
3. Crear labels en Gmail: "Guard-IA: Suspicious", "Guard-IA: Phishing", "Guard-IA: Safe"
4. Después del pipeline, si verdict=WARNED, aplicar label "Suspicious" al email en Gmail
5. Configurar en `policy_service.py` o como nueva acción automática

---

### TAREA 7: Entrega de alertas (🟡 Alta)

**Estado actual**: `alert_service.py` crea AlertEvents con `delivery_status=PENDING` pero no los envía.

**Pasos**:
1. Implementar `AlertDeliveryWorker` (async background task)
2. Para channel=EMAIL: enviar via SMTP (aiosmtplib) al CISO
3. Para channel=SLACK: POST a Slack webhook URL
4. Actualizar `delivery_status` a DELIVERED/FAILED
5. Integrar con el pipeline (llamar `evaluate_and_fire` después de cada análisis)

---

### TAREA 8: Benchmark de heurísticas (🟡 Alta)

**Estado actual**: Motor heurístico funciona pero no hay evaluación formal.

**Pasos**:
1. Usar el mismo dataset de la Tarea 1 como ground truth
2. Ejecutar todas las heurísticas contra el dataset
3. Calcular precision/recall/F1 del motor heurístico solo
4. Documentar fortalezas/debilidades (ej: bueno en auth checks, débil en BEC sin typosquatting)
5. Usar como baseline para comparar con el modelo ML

---

## 4. Progreso General v0.2

```
Integración Google Workspace:  ██████████░░░░░ 70%  (infra lista, falta ruteo real)
Modelo ML clasificación:       ████░░░░░░░░░░░ 30%  (code listo, falta dataset+training)
Acciones automáticas:          ████████░░░░░░░ 55%  (SMTP actions OK, falta Gmail API + alertas)
Dashboard v0:                  ██████████████░ 85%  (funcional, falta sender view + reports UI)
Documentación datos/métricas:  ██████░░░░░░░░░ 40%  (schema docs OK, falta plan ML)
```

**Progreso estimado total v0.2: ~55%**
