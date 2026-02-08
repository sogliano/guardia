# Guard-IA - Tareas Jira Retroactivas

**Proyecto:** Guard-IA - AI-powered pre-delivery email fraud detection middleware
**Período:** 20 Diciembre 2025 - 15 Febrero 2026
**Autor:** Strike Security - Universidad ORT Uruguay
**Total Tareas:** 75 issues (2 Epics, 18 Stories, 55 Tasks)

---

# EPIC: GUARD-1 - Release v0.1 Walking Skeleton

**Fecha Inicio:** 20/12/2025
**Fecha Fin:** 16/01/2026

**Descripción:**

Implementar un sistema funcional end-to-end mínimo que permita ingestar emails, analizarlos con reglas heurísticas básicas, y visualizar resultados en un frontend de prueba de concepto. El objetivo es validar la arquitectura completa del sistema con funcionalidad reducida pero operativa.

**Entregables:**
- Backend FastAPI con modelos base de datos (Email, Case, Analysis)
- Pipeline de análisis con heurísticas básicas
- Frontend Vue 3 con vistas de Dashboard y Cases (mockup)
- Infraestructura Docker para desarrollo local
- Integración end-to-end funcional
- Validación con cliente Strike Security

---

## GUARD-2: Setup inicial proyecto FastAPI

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 20/12/2025
**Fecha Fin:** 21/12/2025

**Descripción:**

Inicializar el proyecto backend con FastAPI, estableciendo la estructura de carpetas siguiendo mejores prácticas de arquitectura modular. Configurar el entorno de desarrollo con Python 3.11, dependencias base (FastAPI, Uvicorn, Pydantic v2), y sistema de configuración mediante variables de entorno. Incluir endpoint de health check para verificar que el servidor funciona correctamente.

---

## GUARD-3: Configuración PostgreSQL con Docker

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 21/12/2025
**Fecha Fin:** 22/12/2025

**Descripción:**

Configurar PostgreSQL 16 como base de datos principal usando Docker Compose. Establecer volúmenes persistentes para datos, configurar credenciales seguras mediante variables de entorno, y crear script de inicialización. Verificar conectividad desde el backend y asegurar que el servicio se levanta automáticamente con `make dev`.

---

## GUARD-4: Modelos SQLAlchemy async (Email, Case, Analysis)

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 22/12/2025
**Fecha Fin:** 24/12/2025

**Descripción:**

Implementar los modelos de base de datos core usando SQLAlchemy async con asyncpg como driver. El modelo Email almacena emails crudos con headers en JSONB. El modelo Case representa un caso de análisis vinculado 1:1 con Email, incluyendo status, scores y veredicto. El modelo Analysis almacena resultados de cada etapa del pipeline (heuristic, ml, llm) con metadata en JSONB. Establecer relaciones FK y crear índices en columnas de búsqueda frecuente.

---

## GUARD-5: Configuración Alembic para migraciones

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 24/12/2025
**Fecha Fin:** 24/12/2025

**Descripción:**

Configurar Alembic como sistema de migraciones de base de datos con soporte async. Configurar `env.py` para trabajar con el engine async de SQLAlchemy. Generar migración inicial autogenerada para los modelos Email, Case y Analysis. Crear comandos make para ejecutar migraciones (`make migrate`) y crear nuevas (`make migration msg="descripcion"`).

---

## GUARD-6: Diseño arquitectura de pipeline de análisis

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 23/12/2025
**Fecha Fin:** 24/12/2025

**Descripción:**

Diseñar la arquitectura modular del pipeline de análisis de emails con 3 etapas independientes: Heuristic, ML y LLM. Definir el flujo orquestado por un servicio central (Orchestrator) que ejecuta cada etapa secuencialmente, calcula score final ponderado, y determina veredicto según thresholds. Establecer interfaces estándar para scorers (`analyze(email) → AnalysisResult`) y documentar pesos iniciales (Heuristic 40%, ML 40%, LLM 20%) y thresholds de decisión (ALLOW < 0.3, WARN 0.3-0.6, QUARANTINE 0.6-0.8, BLOCK ≥ 0.8).

---

## GUARD-7: Implementación HeuristicEngine básico

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 25/12/2025
**Fecha Fin:** 27/12/2025

**Descripción:**

Implementar motor de heurísticas con 4 sub-engines especializados: AuthAnalyzer (verifica SPF/DKIM/DMARC y reply-to mismatch), DomainAnalyzer (blacklist check, typosquatting, TLDs sospechosos), URLAnalyzer (shorteners, URLs con IP, dominios sospechosos), y KeywordAnalyzer (urgencia, términos phishing, CAPS abuse). Cada sub-engine genera un score ponderado (Auth 35%, Domain 25%, URL 25%, Keyword 15%). Generar Evidence items por cada hallazgo para auditoría. Objetivo de latencia: <10ms por análisis.

---

## GUARD-8: Modelo Evidence y tipos de evidencia

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 27/12/2025
**Fecha Fin:** 28/12/2025

**Descripción:**

Crear modelo Evidence vinculado a Analysis para almacenar hallazgos detallados. Definir enum EvidenceType con 50+ tipos categorizados (auth_*, domain_*, url_*, keyword_*, attachment_*, header_*). Incluir campos: type, severity (low/medium/high/critical), description, y raw_data JSONB para contexto adicional (URL completa, header original, etc.). Establecer índice en analysis_id para queries eficientes.

---

## GUARD-9: Tests unitarios de heurísticas

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 28/12/2025
**Fecha Fin:** 29/12/2025

**Descripción:**

Desarrollar suite de tests unitarios con pytest para cada sub-engine de heurísticas. Crear fixtures con emails de ejemplo que disparan cada tipo de evidencia (SPF fail, DKIM fail, blacklist hit, typosquatting, shorteners, urgency keywords). Objetivo de coverage >80% en módulo heuristics. Configurar `make test` para ejecutar pytest con reporte de coverage.

---

## GUARD-10: Docker Compose para desarrollo local

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 29/12/2025
**Fecha Fin:** 30/12/2025

**Descripción:**

Consolidar `docker-compose.yml` con todos los servicios necesarios para desarrollo: backend (port 8000), db (port 5432), y preparar estructura para frontend futuro. Configurar redes internas, volúmenes persistentes para PostgreSQL, y code mount para backend con hot reload. Crear comando `make dev` que levanta todos los servicios y centraliza logs.

---

## GUARD-11: Endpoints REST básicos para Cases

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 30/12/2025
**Fecha Fin:** 31/12/2025

**Descripción:**

Implementar endpoints CRUD básicos para gestión de casos: `GET /api/v1/cases` con paginación (page, size) y `GET /api/v1/cases/{id}` para detalle individual. Crear schemas Pydantic v2 (CaseResponse, CaseList) para validación de entrada/salida. Implementar filtros básicos por status, date_from, date_to. Generar documentación automática en Swagger (`/docs`).

---

## GUARD-12: Setup de pytest async

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 31/12/2025
**Fecha Fin:** 01/01/2026

**Descripción:**

Configurar pytest con soporte async (pytest-asyncio) estableciendo `asyncio_mode=auto` en pytest.ini. Crear conftest.py con fixtures reutilizables: async_db_session (SQLite temporal para tests), test_client (FastAPI TestClient). Desarrollar tests de ejemplo para endpoints básicos. Configurar pytest-cov para reportes de coverage. Integrar en `make test`.

---

## GUARD-13: Fix encoding UTF-8 en body_html de emails

**Tipo:** Bug
**Epic:** GUARD-1
**Fecha Inicio:** 01/01/2026
**Fecha Fin:** 02/01/2026

**Descripción:**

Resolver problema de UnicodeDecodeError al persistir emails con caracteres especiales (tildes, ñ) en PostgreSQL. El parser de email estaba usando decode incorrecto. Implementar `email.policy.default` en parser para manejo correcto de UTF-8. Agregar test de regresión con email en español.

---

## GUARD-14: Makefile con comandos de desarrollo

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 02/01/2026
**Fecha Fin:** 02/01/2026

**Descripción:**

Crear Makefile con comandos de desarrollo más usados: `make dev` (levanta docker compose), `make test` (ejecuta pytest), `make lint` (ruff + mypy), `make migrate` (alembic upgrade head), `make migration msg=""` (crea nueva migración). Documentar todos los comandos en README.md. Usar .PHONY para evitar conflictos con archivos del sistema.

---

## GUARD-15: Setup proyecto Vue 3 + TypeScript

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 03/01/2026
**Fecha Fin:** 04/01/2026

**Descripción:**

Inicializar proyecto frontend con Vue 3, TypeScript y Vite como bundler. Configurar Composition API con script setup, TypeScript en modo strict, y estructura de carpetas modular (views/, components/, stores/, services/, types/). Establecer path alias `@/` apuntando a `src/`. Configurar Vite proxy para desarrollo hacia backend (localhost:8000).

---

## GUARD-16: Componentes base de UI (AppLayout, Sidebar)

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 04/01/2026
**Fecha Fin:** 05/01/2026

**Descripción:**

Crear componentes de layout reutilizables: AppLayout.vue (estructura con sidebar fijo + área de contenido) y AppSidebar.vue (navegación con iconos Material Symbols). Implementar navegación a rutas Dashboard, Cases, Emails. Diseño responsive con sidebar que colapsa en mobile. Definir CSS variables del design system (colores primarios, texto, acentos).

---

## GUARD-17: Vista Dashboard con KPIs mockup

**Tipo:** Story
**Epic:** GUARD-1
**Fecha Inicio:** 05/01/2026
**Fecha Fin:** 07/01/2026

**Descripción:**

Implementar vista de Dashboard inicial con KPIs estáticos (datos hardcodeados) para validar layout y UX antes de integrar con API real. Crear componente StatsCard reutilizable que acepta props (icon, iconColor, label, value, trend, details). Mostrar 4 KPIs principales: Total Emails Analyzed, Threats Detected, Avg Response Time, Blocked/Quarantined. Layout responsive con grid de 4 columnas en desktop, 2 en mobile.

---

## GUARD-18: Pinia store para Cases

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 06/01/2026
**Fecha Fin:** 07/01/2026

**Descripción:**

Crear Pinia store para gestionar estado de casos en el frontend. State incluye: cases[] (array de casos), total (count total), page/size (paginación), loading (estado de carga). Implementar actions: fetchCases() (llama API y actualiza state), setPage(), setSize(), setFilters(). Usar setup syntax con ref() para primitivos y reactive() para objetos. Manejar estados de loading y error.

---

## GUARD-19: Vista Cases con tabla básica

**Tipo:** Story
**Epic:** GUARD-1
**Fecha Inicio:** 07/01/2026
**Fecha Fin:** 09/01/2026

**Descripción:**

Implementar vista de lista de casos con tabla HTML mostrando columnas: ID, Subject, Sender, Score, Risk, Verdict, Status, Date. Obtener datos del store cases.ts. Implementar paginación básica con botones Previous/Next. Click en fila muestra alert con ID del caso (navegación a detalle se implementará después). Color coding de score, risk y verdict según design system.

---

## GUARD-20: Servicio API client con Axios

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 08/01/2026
**Fecha Fin:** 09/01/2026

**Descripción:**

Configurar Axios como cliente HTTP base para todas las llamadas API. Crear instancia con baseURL desde variable de entorno `VITE_API_BASE_URL`. Implementar interceptores: request (para inyectar tokens de autenticación futuros), response (manejo automático de errores 401). Configurar timeout de 30s y headers por defecto (Content-Type: application/json).

---

## GUARD-21: caseService.ts con métodos API

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 09/01/2026
**Fecha Fin:** 10/01/2026

**Descripción:**

Crear servicio de casos con métodos typed para comunicación con API: `fetchCases(params)` retorna CaseList, `fetchCase(id)` retorna Case individual. Definir tipos TypeScript correspondientes (Case, CaseList) en types/case.ts. Usar async/await con manejo de errores try-catch. Exportar funciones individualmente para tree-shaking.

---

## GUARD-22: Endpoint POST /emails/ingest

**Tipo:** Story
**Epic:** GUARD-1
**Fecha Inicio:** 10/01/2026
**Fecha Fin:** 12/01/2026

**Descripción:**

Implementar endpoint para ingestar emails en formato MIME. Parsear email raw usando librería estándar de Python (email.message_from_string) extrayendo sender, recipient, subject, body (text/html), headers. Persistir en modelo Email. Disparar pipeline de análisis de forma asíncrona usando BackgroundTasks de FastAPI para no bloquear la respuesta. Retornar 202 Accepted con email_id.

---

## GUARD-23: Orchestrator.analyze() - Pipeline completo

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 11/01/2026
**Fecha Fin:** 13/01/2026

**Descripción:**

Implementar orquestador de pipeline que coordina ejecución de etapas de análisis. Flujo: crear Case con status=PENDING, ejecutar HeuristicEngine.analyze(), calcular final_score (por ahora solo heuristic, ML/LLM vendrán después), determinar verdict según thresholds, calcular risk_level (LOW/MEDIUM/HIGH/CRITICAL), persistir Case + Analysis + Evidences, actualizar status=ANALYZED. Implementar manejo de excepciones por etapa y logging estructurado con structlog.

---

## GUARD-24: Tests end-to-end del flujo completo

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 13/01/2026
**Fecha Fin:** 14/01/2026

**Descripción:**

Desarrollar test de integración que verifica el flujo completo desde ingesta hasta persistencia. Test hace POST a /emails/ingest con email de prueba, verifica creación de Email en DB, valida que Case tiene status=ANALYZED, confirma que Analysis tiene score > 0, y verifica presencia de Evidence items. Crear dos casos: email phishing (score alto) y email legítimo (score bajo). Usar fixtures de emails en tests/fixtures/.

---

## GUARD-25: Demo interna v0.1

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 14/01/2026
**Fecha Fin:** 14/01/2026

**Descripción:**

Realizar presentación interna del walking skeleton funcional al equipo. Grabar video de 5 minutos mostrando flujo completo: ingest de email → visualización en Cases → inspección de score. Recolectar notas de feedback del equipo. Identificar bugs y mejoras prioritarias para siguiente fase.

---

## GUARD-26: Fix CORS en backend para frontend local

**Tipo:** Bug
**Epic:** GUARD-1
**Fecha Inicio:** 15/01/2026
**Fecha Fin:** 15/01/2026

**Descripción:**

Resolver error CORS que impide requests desde frontend (localhost:3000) hacia backend. Configurar CORSMiddleware de FastAPI en main.py permitiendo origen http://localhost:3000, métodos GET/POST/PUT/DELETE, y headers wildcard para desarrollo. En producción, CORS_ORIGINS se cargará desde variable de entorno para mayor seguridad.

---

## GUARD-27: Validación con cliente (Strike Security)

**Tipo:** Story
**Epic:** GUARD-1
**Fecha Inicio:** 15/01/2026
**Fecha Fin:** 16/01/2026

**Descripción:**

Realizar sesión de validación de 1 hora con cliente Strike Security para demostrar Release v0.1. Ejecutar demo en vivo del sistema funcionando end-to-end. Documentar feedback en Confluence. Priorizar features sugeridas para Release v0.2. Obtener sign-off formal del milestone v0.1 como validación de que la arquitectura y approach son correctos.

---

## GUARD-28: Retrospectiva Sprint 2

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 16/01/2026
**Fecha Fin:** 16/01/2026

**Descripción:**

Realizar retrospectiva del equipo sobre el período de desarrollo de v0.1. Reunión de 45 minutos usando formato Start/Stop/Continue para identificar qué funcionó bien y qué mejorar. Documentar action items concretos para implementar en próximo período. Registrar notas en Confluence.

---

# EPIC: GUARD-29 - Release v0.2 Integración Real + Modelo Base

**Fecha Inicio:** 17/01/2026
**Fecha Fin:** 15/02/2026

**Descripción:**

Evolucionar el sistema a una versión production-ready integrando autenticación real con Clerk, modelo de Machine Learning DistilBERT fine-tuned, LLM explainer para análisis semántico profundo, dashboard completo con métricas en tiempo real, vista de monitoring con tabs por etapa del pipeline, y deploy funcional en Google Cloud Platform. Esta release convierte el walking skeleton en un sistema completo y operativo.

**Entregables:**
- Autenticación con Clerk (JWT RS256, JIT provisioning)
- Pipeline ML: DistilBERT 66M params fine-tuned para clasificación phishing
- LLM Explainer: OpenAI GPT-4o con structured output
- Dashboard con KPIs reales y charts (Chart.js)
- Vista Monitoring con 3 tabs (Heuristics, ML, LLM)
- Deploy en GCP (Cloud Run + CloudSQL)
- Validación final con cliente

---

## GUARD-30: Investigación integración Google Workspace API

**Tipo:** Spike
**Epic:** GUARD-29
**Fecha Inicio:** 17/01/2026
**Fecha Fin:** 18/01/2026

**Descripción:**

Investigar viabilidad técnica de integración con Google Workspace API (Gmail) para interceptar emails pre-delivery. Realizar prueba de concepto leyendo emails via API. Evaluar permisos OAuth requeridos y limitaciones de la API. Documentar findings en documento técnico. Resultado: decisión de usar SMTP gateway (aiosmtpd) en lugar de API directa por mayor flexibilidad y control del flujo pre-delivery.

---

## GUARD-31: Setup de Clerk para autenticación

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 18/01/2026
**Fecha Fin:** 19/01/2026

**Descripción:**

Configurar Clerk como proveedor de autenticación del sistema. Crear aplicación en Clerk dashboard. Obtener y configurar keys: CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, CLERK_PEM_PUBLIC_KEY (para verificación JWT RS256). Configurar frontend con @clerk/vue (ClerkProvider envuelve App.vue). Configurar backend para verificar JWT RS256 usando PyJWT con clave pública.

---

## GUARD-32: Modelo User y sync con Clerk

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 19/01/2026
**Fecha Fin:** 20/01/2026

**Descripción:**

Crear modelo User local sincronizado con Clerk mediante JIT (Just In Time) provisioning. Campos: clerk_id (unique), email, full_name, role (default: analyst), is_active. Implementar servicio UserSyncService.sync_clerk_user() que en primer login del usuario crea registro local consultando Clerk API. Actualizar last_login_at en cada autenticación. Establecer relaciones FK: User → Case (created_by, resolved_by).

---

## GUARD-33: Middleware de autenticación JWT

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 20/01/2026
**Fecha Fin:** 21/01/2026

**Descripción:**

Implementar middleware que extrae y verifica JWT de Clerk en cada request. HTTPBearer extrae token del header Authorization. Función security.verify_clerk_token() verifica JWT usando clave pública RS256, validando claims exp, nbf, sub. Dependency deps.get_current_user() retorna User autenticado, lanzando UnauthorizedError si token inválido. Endpoints protegidos usan Depends(get_current_user).

---

## GUARD-34: Endpoints protegidos con roles

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 21/01/2026
**Fecha Fin:** 22/01/2026

**Descripción:**

Agregar sistema de autorización basado en roles (administrator, analyst, auditor). Implementar dependency factory require_role(*allowed_roles) con shortcuts RequireAdmin, RequireAnalyst. Proteger endpoints sensibles: resolve_case requiere analyst o superior, endpoints de settings requieren admin. Desarrollar tests de autorización verificando que usuarios sin rol correcto reciben 403 Forbidden.

---

## GUARD-35: Evaluación modelos ML para clasificación phishing

**Tipo:** Spike
**Epic:** GUARD-29
**Fecha Inicio:** 22/01/2026
**Fecha Fin:** 23/01/2026

**Descripción:**

Realizar benchmark comparativo de modelos candidatos para clasificación ML: DistilBERT, BERT, RoBERTa. Evaluar con dataset pequeño (1000 phishing + 1000 legit) midiendo accuracy, precision, recall, latencia de inferencia, y tamaño del modelo. Resultado: DistilBERT (66M params) elegido por mejor balance accuracy/velocidad (~18ms latencia, 260MB modelo vs ~40ms y 440MB de BERT). Documentar decisión técnica y metas de tesis (Precision ≥98.66%, Recall ≥99.57%).

---

## GUARD-36: Setup MLflow para tracking de modelos

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 23/01/2026
**Fecha Fin:** 24/01/2026

**Descripción:**

Configurar servidor MLflow para tracking de experimentos, parámetros, métricas y artifacts de modelos. Levantar MLflow en localhost:5000 con backend SQLite. Agregar servicio mlflow a docker-compose.yml. Crear experimento "guardia-distilbert". Configurar backend para conectar con MLFLOW_TRACKING_URI. Verificar que UI de MLflow es accesible y puede registrar runs.

---

## GUARD-37: Fine-tuning DistilBERT para clasificación

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 24/01/2026
**Fecha Fin:** 26/01/2026

**Descripción:**

Realizar fine-tuning de DistilBERT base (distilbert-base-uncased) para clasificación binaria phishing/legit. Crear script ml/src/train.py usando Hugging Face Trainer API. Dataset splits: 80% train, 10% val, 10% test (estratificados). Hiperparámetros: 3 epochs, batch=8, learning_rate=5e-5, max_sequence_length=256. Implementar EarlyStoppingCallback con patience=2. Loguear métricas en MLflow (accuracy, precision, recall, F1, loss). Guardar modelo en ml/models/distilbert-guardia/. Validar accuracy test > 95%.

---

## GUARD-38: MLClassifier service con singleton pattern

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 26/01/2026
**Fecha Fin:** 27/01/2026

**Descripción:**

Implementar servicio MLClassifier que carga modelo una sola vez (singleton thread-safe) y expone método analyze() async. Lazy loading del modelo usando Lock para evitar race conditions. Método analyze(email_text) → (score, confidence). Carga async con asyncio.to_thread() para no bloquear event loop. Graceful degradation: si modelo no existe en ML_MODEL_PATH, retorna score=0.0 sin crashear. Loguear latencia por request.

---

## GUARD-39: Integración ML en pipeline orchestrator

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 27/01/2026
**Fecha Fin:** 28/01/2026

**Descripción:**

Actualizar orchestrator para ejecutar ML classifier como segunda etapa del pipeline (después de heuristics, antes de LLM). Ajustar cálculo de score final con nuevos pesos: Heuristic 30%, ML 50%, LLM 20%. ML genera Analysis con stage=ML. Si score ML > 0.7, crear Evidence tipo ML_HIGH_SCORE. Actualizar tests para validar pipeline multi-stage. Si ML falla, redistribuir pesos automáticamente.

---

## GUARD-40: Setup OpenAI API para LLM explainer

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 28/01/2026
**Fecha Fin:** 29/01/2026

**Descripción:**

Configurar cliente OpenAI para análisis LLM de emails. Establecer OPENAI_API_KEY en .env. Crear prompt system contextualizado con información de Strike Security, dominios conocidos legítimos, y categorías de amenaza. Implementar structured output usando response_format de OpenAI para obtener score (float 0-1) y explanation (string). Usar modelo gpt-4o-mini (costo-eficiente). Temperatura 0 para outputs deterministas.

---

## GUARD-41: LLMExplainer service e integración en pipeline

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 29/01/2026
**Fecha Fin:** 30/01/2026

**Descripción:**

Implementar servicio LLMExplainer que analiza email y genera score + explicación humana. Método analyze(email_text) → (score, explanation). Timeout de 10s para llamada OpenAI. Retry logic con backoff exponencial (3 intentos). Integrar en pipeline como última etapa. Guardar explanation en Analysis.explanation. Loguear costo estimado por request. Fallback: si LLM falla, pipeline continúa usando solo Heuristic+ML.

---

## GUARD-42: Fix deadlock en carga singleton ML model

**Tipo:** Bug
**Epic:** GUARD-29
**Fecha Inicio:** 30/01/2026
**Fecha Fin:** 30/01/2026

**Descripción:**

Resolver deadlock causado por requests concurrentes en get_ml_classifier(). Lock estaba creándose dentro de función, causando lock per-invocation. Solución: mover Lock a nivel de módulo (global) e implementar double-checked locking pattern (verificar `if _instance is None` antes y después de adquirir lock). Validar con test de carga de 10 requests simultáneos.

---

## GUARD-43: Rediseño Dashboard con KPIs reales desde API

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 31/01/2026
**Fecha Fin:** 02/02/2026

**Descripción:**

Reimplementar Dashboard reemplazando datos mockup por datos reales del endpoint /api/v1/dashboard. Implementar endpoint que agrega métricas: total emails, threats detected, blocked/quarantined, avg response time. Crear componentes Chart.js: ThreatChart (line chart de amenazas por día), RiskDistribution (pie chart de distribución de riesgo), RecentCases (tabla de últimos 10 casos). Implementar store dashboard.ts con action fetchDashboard(). Aplicar colores del design system de forma consistente.

---

## GUARD-44: Vista Monitoring con 3 tabs (Heuristics, ML, LLM)

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 02/02/2026
**Fecha Fin:** 04/02/2026

**Descripción:**

Implementar vista completa de Monitoring con tabs separados por etapa del pipeline. Tab Heuristics: total runs, avg latency, top 10 rules triggered, score distribution. Tab ML: total calls, avg latency, confidence vs accuracy scatter plot, error rate. Tab LLM: total calls, tokens usage trend, cost breakdown por modelo, latency distribution. Implementar endpoint GET /api/v1/monitoring?tab=llm|ml|heuristics. Crear 11 componentes de charts especializados. Store monitoring.ts gestiona activeTab state. Integrar con GlobalFiltersBar para filtrado por fecha.

---

## GUARD-45: GlobalFiltersBar component con date range

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 03/02/2026
**Fecha Fin:** 04/02/2026

**Descripción:**

Crear componente de filtros globales con selector de rango de fechas compartido entre todas las vistas. Presets disponibles: All time, Last 30 days, Last 7 days, Last 24 hours, Custom (abre modal con date pickers). Store globalFilters.ts sincroniza date_from/date_to. Todas las vistas (Dashboard, Monitoring, Cases) reaccionan automáticamente a cambios de filtro usando watch(). Usar <input type="date"> nativo para custom range.

---

## GUARD-46: Vista Email Explorer con filtros avanzados

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 04/02/2026
**Fecha Fin:** 05/02/2026

**Descripción:**

Implementar vista de exploración y búsqueda de emails con tabla, filtros múltiples, y paginación server-side. Search bar con debounce de 300ms filtra por subject/sender. Filtros dropdown: Show All/With Case/No Case, Risk Level, Date Range. Paginación server-side (page, size) con controles Previous/Next. Click en fila navega a CaseDetail si email tiene caso asociado. Store emails.ts con fetchEmails(). Highlight visual de filas según risk_level.

---

## GUARD-47: CaseDetailView con análisis completo

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 05/02/2026
**Fecha Fin:** 07/02/2026

**Descripción:**

Implementar vista de detalle completo de caso mostrando toda la información disponible. Implementar endpoint GET /api/v1/cases/{id}/detail que retorna Case + Email + Analyses + Evidences + Notes + FPReviews. Email preview renderiza headers y body (HTML en iframe sandbox, texto plano). Tres secciones accordion de análisis (Heuristic, ML, LLM) mostrando scores, confidence, explanation. Tabla de evidencias expandible agrupada por tipo. Sección de notas con formulario para agregar/editar. Botón "Resolve Case" abre modal de veredicto. Si veredicto fue falso positivo, mostrar formulario de FP Review.

---

## GUARD-48: Componente QuarantineQueue para casos cuarentenados

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 06/02/2026
**Fecha Fin:** 07/02/2026

**Descripción:**

Crear componente QuarantineQueue.vue como tab en Cases view mostrando emails cuarentenados con acciones disponibles. Tabla de casos con verdict=QUARANTINED. Botones de acción: Release (liberar email, relay a destino), Keep (confirmar bloqueo permanente), Delete (eliminar email). Implementar endpoints POST /quarantine/{id}/release|keep|delete. Modal de confirmación solicita campo reason. Mostrar notificación toast en acción exitosa. Actions mutan store cases directamente.

---

## GUARD-49: Deploy en GCP Cloud Run (staging)

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 07/02/2026
**Fecha Fin:** 08/02/2026

**Descripción:**

Realizar primer deploy de backend y frontend en Google Cloud Platform usando Cloud Run. Configurar CloudSQL con PostgreSQL 16. Crear Dockerfile optimizado con multi-stage build para reducir tamaño de imagen. Desplegar backend en europe-west1 con autoscaling 1-10 instancias. Configurar CloudSQL proxy para conexión segura. Establecer URLs: backend.guardia.strike.security, app.guardia.strike.security. Deploy de frontend como servicio separado en Cloud Run.

---

## GUARD-50: Configuración de variables de entorno en producción

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 08/02/2026
**Fecha Fin:** 08/02/2026

**Descripción:**

Migrar variables de entorno de .env local a Secret Manager de GCP. Crear secretos: DB_PASSWORD, CLERK_SECRET_KEY, OPENAI_API_KEY, MLFLOW_TRACKING_URI. Configurar Cloud Run para montar secretos como variables de entorno. Crear .env.production.example documentando variables requeridas. Implementar validación de REQUIRED_ENV_VARS al inicio del backend que falla fast si faltan keys críticas. Verificar que no hay keys hardcodeadas en código.

---

## GUARD-51: Makefile target para deploy

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 08/02/2026
**Fecha Fin:** 09/02/2026

**Descripción:**

Crear comandos make para automatizar deploy a GCP. `make deploy-backend` ejecuta gcloud builds submit + gcloud run deploy para backend. `make deploy-frontend` similar para frontend. Variables de configuración (región, proyecto) en .env.deploy. Documentar comandos y flags de gcloud en README. Flags importantes: --platform managed, --region, --image, --set-env-vars.

---

## GUARD-52: Fix timeout en LLM requests en producción

**Tipo:** Bug
**Epic:** GUARD-29
**Fecha Inicio:** 09/02/2026
**Fecha Fin:** 09/02/2026

**Descripción:**

Resolver timeouts de LLM requests en producción (>30s) causados por latencia de red GCP → OpenAI. Aumentar timeout a 60s para LLM calls. Implementar retry logic con backoff exponencial usando librería tenacity (3 intentos). Agregar logging detallado de latencias por intento. Asegurar fallback: si LLM falla completamente después de retries, pipeline continúa sin score LLM.

---

## GUARD-53: Monitoreo básico de logs en GCP

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 09/02/2026
**Fecha Fin:** 10/02/2026

**Descripción:**

Configurar Cloud Logging para backend y crear dashboard básico en Cloud Monitoring. Configurar structlog con JSONRenderer para generar logs parseables. Crear filtros en Cloud Logging por severity: ERROR, WARNING, INFO. Dashboard con métricas clave: requests/min, latency p50/p95, error rate. Configurar alerta si error_rate > 5% enviando notificación a Slack.

---

## GUARD-54: Testing end-to-end en staging

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 10/02/2026
**Fecha Fin:** 11/02/2026

**Descripción:**

Desarrollar suite de tests E2E que corren contra entorno staging. Crear scripts en tests/e2e/. Test 1: ingest email → verificar aparece en Dashboard. Test 2: resolve case → verificar estado actualizado en DB. Test 3: quarantine actions (release/keep/delete). Usar Playwright para tests de frontend y pytest para tests de API. Todos los tests deben pasar antes de deploy a producción. Integrar en CI/CD pipeline.

---

## GUARD-55: Release v0.2 y tag en Git

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 11/02/2026
**Fecha Fin:** 11/02/2026

**Descripción:**

Crear release v0.2 oficial en GitHub. Crear tag v0.2 en rama main. Escribir release notes detalladas listando features nuevas (auth, ML, LLM, monitoring). Actualizar CHANGELOG.md con secciones Added, Changed, Fixed. Enviar email a stakeholders con link a release y highlights. Grabar demo video de 10 minutos mostrando sistema completo funcionando.

---

## GUARD-56: Fix header uppercase en Dashboard y Monitoring

**Tipo:** Bug
**Epic:** GUARD-29
**Fecha Inicio:** 12/02/2026
**Fecha Fin:** 12/02/2026

**Descripción:**

Corregir bug visual donde títulos en Dashboard y Monitoring aparecen en MAYÚSCULAS por CSS incorrecto. Remover propiedad `text-transform: uppercase` de `.header-left h1`. Verificar que títulos quedan consistentes con Cases y Email Explorer. Validar cambio en staging antes de deploy a producción.

---

## GUARD-57: Fix tooltip de score en Cases tables

**Tipo:** Bug
**Epic:** GUARD-29
**Fecha Inicio:** 12/02/2026
**Fecha Fin:** 12/02/2026

**Descripción:**

Eliminar tooltip no solicitado de columna SCORE en tablas de Cases que mostraba breakdown de Heuristic/ML/LLM al hacer hover. Remover ícono info y div .score-tooltip de 3 tabs: All Cases, Needs Action, Quarantine. Eliminar CSS relacionado (.score-cell, .score-detail-icon, .score-tooltip). Simplificar a mostrar solo score final. Detalles de breakdown quedan disponibles en CaseDetail view.

---

## GUARD-58: Validación con cliente (Strike Security) - v0.2

**Tipo:** Story
**Epic:** GUARD-29
**Fecha Inicio:** 13/02/2026
**Fecha Fin:** 13/02/2026

**Descripción:**

Realizar sesión de validación final de 1.5 horas con cliente Strike Security para Release v0.2. Demo completo del sistema: Dashboard, Cases management, Monitoring (3 tabs), Email Explorer, Quarantine queue. Mostrar flujo end-to-end: ingest → pipeline 3 etapas (Heuristic+ML+LLM) → visualización en todas las vistas. Usar entorno staging con datos reales simulados (10+ emails variados). Documentar feedback y obtener sign-off formal del milestone v0.2.

---

## GUARD-59: Retrospectiva y cierre v0.2

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 13/02/2026
**Fecha Fin:** 13/02/2026

**Descripción:**

Realizar retrospectiva final del período de desarrollo de Release v0.2 y celebración de cierre. Reunión de 1 hora revisando objetivos: ✅ autenticación, ✅ ML, ✅ LLM, ✅ dashboard, ✅ monitoring, ✅ deploy GCP. Calcular métricas del período: velocity, bugs resueltos, stories completadas. Documentar lecciones aprendidas para futuros desarrollos. Planificar features de v0.3 según feedback de cliente. Formato: Timeline retrospective. Celebración: team dinner virtual.

---

# TAREAS COMPLEMENTARIAS

## GUARD-60: Modelo Evidence expandido a 50+ tipos

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 27/12/2025
**Fecha Fin:** 28/12/2025

**Descripción:**

Expandir enum EvidenceType a 50+ categorías para cubrir exhaustivamente todos los hallazgos posibles del pipeline. Categorías: auth_* (SPF/DKIM/DMARC failures), domain_* (blacklist, typosquatting, suspicious TLD), url_* (shorteners, IP-based, malformed), keyword_* (urgency, phishing, financial, BEC), attachment_* (suspicious extension, double extension), header_* (received hops, suspicious mailer), ml_* (high score, low confidence), llm_* (high score, explanation flags). Documentar cada tipo en docstrings. Crear tests de creación de evidencias por tipo.

---

## GUARD-61: Modelo AlertRule y AlertEvent

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 25/01/2026
**Fecha Fin:** 26/01/2026

**Descripción:**

Implementar sistema de alertas configurables. Modelo AlertRule: name, description, severity (low/medium/high/critical), conditions (JSONB con expresiones evaluables), channels (list: slack/email/webhook), is_active. Modelo AlertEvent: alert_rule_id FK, case_id FK (opcional), severity, channel, delivery_status, trigger_info JSONB (contexto de disparo). Establecer relación AlertRule → AlertEvent (1:N). Implementar endpoints CRUD para gestión de AlertRules.

---

## GUARD-62: Modelo PolicyEntry (whitelist/blacklist)

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 26/01/2026
**Fecha Fin:** 27/01/2026

**Descripción:**

Crear modelo para gestionar listas de permitidos/bloqueados. PolicyEntry: list_type (whitelist/blacklist), entry_type (domain/ip/sender), value (string del domain/ip/email), is_active, added_by (FK User). Integrar BypassChecker en pipeline que verifica whitelist antes de análisis completo. Si dominio está en whitelist y SPF/DKIM pasan, bypass completo (score=0, verdict=ALLOWED). Implementar endpoints CRUD para policies. Tests de bypass logic.

---

## GUARD-63: Modelo Notification para notificaciones in-app

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 05/02/2026
**Fecha Fin:** 06/02/2026

**Descripción:**

Implementar sistema de notificaciones in-app para usuarios. Modelo Notification: user_id FK, type (case_new/alert_triggered/system), severity (info/warning/error), title, message, reference_id/reference_type (link a caso/alerta), is_read (boolean), created_at. Endpoints: GET /api/v1/notifications (lista para usuario actual), PUT /api/v1/notifications/{id}/read (marcar como leída). Store notifications.ts en frontend. Badge de count no leídas en sidebar.

---

## GUARD-64: Integración Slack para alertas

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 08/02/2026
**Fecha Fin:** 09/02/2026

**Descripción:**

Implementar envío de notificaciones de alertas críticas a canal Slack via webhook. SlackService con método send_alert(case, alert_rule). Configurar SLACK_WEBHOOK_URL en env. AlertService dispara mensaje a Slack automáticamente si severity=critical. Formato de mensaje: caso ID, score final, verdict, categoría de amenaza, link directo a CaseDetail. Implementar test con webhook de prueba verificando payload correcto.

---

## GUARD-65: Endpoints de reportería básica

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 10/02/2026
**Fecha Fin:** 11/02/2026

**Descripción:**

Crear endpoints para generación de reportes agregados. GET /api/v1/reports/summary (métricas generales por período), GET /api/v1/reports/threats-by-category (conteo por categoría de amenaza), GET /api/v1/reports/pipeline-performance (latencias y error rates por etapa). Formato JSON con métricas agregadas. Filtros disponibles: date_from, date_to, risk_level, verdict. Preparar estructura para exportación futura a PDF/CSV.

---

## GUARD-66: SMTP Gateway con aiosmtpd

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 18/01/2026
**Fecha Fin:** 19/01/2026

**Descripción:**

Implementar SMTP gateway que intercepta emails entrantes en tiempo real. Server aiosmtpd escuchando en puerto 2525. Handler personalizado procesa cada email: parsea MIME, llama API POST /emails/ingest, espera resultado de pipeline, decide relay o bloqueo. Si verdict=ALLOWED, relay a destino real via aiosmtplib. Si verdict=BLOCKED/QUARANTINED, descarta email y notifica remitente. Agregar servicio smtp-gateway a docker-compose. Comando `make dev-gateway` levanta gateway + backend juntos.

---

## GUARD-67: Simulador de emails para testing

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 11/02/2026
**Fecha Fin:** 12/02/2026

**Descripción:**

Crear script que genera emails de prueba realistas para testing exhaustivo del pipeline. Script ml/src/simulate_emails.py genera 100 emails de cada categoría: phishing genérico, credential phishing, BEC, malware payload, spear phishing, emails limpios. Envía via SMTP gateway o API directa según configuración. Loguea resultados: scores obtenidos, verdicts, categorías detectadas. Comando `make simulate` ejecuta simulación completa. Útil para validar pipeline y generar datos de prueba.

---

## GUARD-68: Fix error 401 en resolve case por token expirado

**Tipo:** Bug
**Epic:** GUARD-29
**Fecha Inicio:** 15/02/2026
**Fecha Fin:** 15/02/2026

**Descripción:**

Resolver problema reportado por usuarios que reciben error 401 al intentar resolver casos después de sesión larga (token Clerk expirado). Implementar refresh automático de token en frontend. Interceptor de Axios detecta 401, llama a Clerk getToken() para obtener token fresco, reintenta request original automáticamente. Usuario no pierde trabajo ni es redirigido a login. Agregar tests de token expiration simulando expiración.

---

## GUARD-69: Documentación de API con Swagger mejorada

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 12/01/2026
**Fecha Fin:** 13/01/2026

**Descripción:**

Mejorar documentación automática de Swagger en `/docs` con información detallada. Todos los endpoints tienen description y summary descriptivos. Schemas Pydantic con Field(..., description="explicación del campo"). Ejemplos de request/response en docstrings de funciones. Tags por recurso (cases, emails, monitoring, dashboard, alerts, policies) para organización clara. Resultado: documentación API profesional y completa accesible en `/docs`.

---

## GUARD-70: README con instrucciones de setup

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 02/01/2026
**Fecha Fin:** 02/01/2026

**Descripción:**

Documentar setup completo del proyecto en README.md para facilitar onboarding. Secciones: Architecture overview, Prerequisites (Python 3.11, Node 18+, Docker), Setup instructions (clone, install, configure .env), Development (make dev, make test), Testing, Deploy. Documentar todos los comandos make disponibles. Listar variables de entorno requeridas con descripciones. Incluir capturas de pantalla del sistema funcionando.

---

## GUARD-71: CLAUDE.md con contexto del proyecto

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 02/01/2026
**Fecha Fin:** 02/01/2026

**Descripción:**

Crear archivo CLAUDE.md con contexto técnico completo del proyecto para Claude Code. Documentar arquitectura: backend (FastAPI/SQLAlchemy), frontend (Vue 3/TypeScript), ml (DistilBERT/MLflow), infra (Docker/GCP). Explicar pipeline: Heuristics → ML → LLM con pesos y thresholds. Coding rules: Python (ruff, mypy, indent 4, line 100), TypeScript (eslint, indent 2). Comandos útiles (make, alembic). Decisiones técnicas clave y su justificación.

---

## GUARD-72: Configuración de ruff y mypy para linting

**Tipo:** Task
**Epic:** GUARD-1
**Fecha Inicio:** 21/12/2025
**Fecha Fin:** 21/12/2025

**Descripción:**

Configurar herramientas de linting para mantener calidad de código. Crear ruff.toml con reglas estrictas: E (errors), F (pyflakes), I (isort), N (naming), W (warnings). Crear mypy.ini con strict=true para type checking riguroso. Comando `make lint` ejecuta ruff check + mypy en secuencia. Configurar pre-commit hook opcional. Integrar linting en CI/CD pipeline para bloquear merges con errores.

---

## GUARD-73: Fix import absolutos en tests

**Tipo:** Bug
**Epic:** GUARD-1
**Fecha Inicio:** 14/01/2026
**Fecha Fin:** 14/01/2026

**Descripción:**

Resolver ModuleNotFoundError en tests causado por imports relativos incorrectos. Estandarizar todos los imports a formato absoluto: `from app.X import Y`. Modificar conftest.py para agregar directorio backend/ a sys.path automáticamente. Tests deben ejecutarse sin configurar PYTHONPATH manualmente. Documentar estructura de imports en README.

---

## GUARD-74: CI/CD con GitHub Actions

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 09/02/2026
**Fecha Fin:** 10/02/2026

**Descripción:**

Implementar pipeline CI/CD completo con GitHub Actions. Crear .github/workflows/ci.yml con jobs: lint (ruff+mypy), test-backend (pytest), test-frontend (vitest/jest). Deploy automático a staging si todos los tests pasan en push a main. Deploy a producción requiere manual approval. Notificaciones en Slack del status de cada pipeline run (success/failure). Cachear dependencias Python/Node para velocidad.

---

## GUARD-75: Métricas de performance del pipeline en DB

**Tipo:** Task
**Epic:** GUARD-29
**Fecha Inicio:** 11/02/2026
**Fecha Fin:** 12/02/2026

**Descripción:**

Implementar persistencia de métricas de performance para análisis histórico. Poblar Analysis.execution_time_ms para cada etapa. Calcular Case.pipeline_duration_ms como suma de todas las etapas. Crear queries agregadas en MonitoringService para calcular p50, p95, p99 de latencias. Endpoint GET /api/v1/metrics/pipeline-performance expone estas métricas. Dashboard de Monitoring consume estos datos para mostrar tendencias de performance en el tiempo.

---

# RESUMEN FINAL

**Total de tareas:** 75
**Período:** 20 Diciembre 2025 - 15 Febrero 2026 (57 días)

**Distribución por tipo:**
- **Epics:** 2 (v0.1, v0.2)
- **Stories:** 18 (funcionalidades con valor usuario)
- **Tasks:** 55 (implementación técnica)
- **Bugs:** 7 (correcciones)
- **Spikes:** 3 (investigación técnica)

**Tecnologías implementadas:**
- Backend: FastAPI, SQLAlchemy async, PostgreSQL 16, DistilBERT, OpenAI GPT-4o, Clerk
- Frontend: Vue 3, TypeScript, Pinia, Chart.js, Axios
- Infraestructura: Docker, GCP Cloud Run, CloudSQL, MLflow, GitHub Actions
- Testing: pytest, Playwright, pytest-cov

**Métricas del pipeline:**
- Latencia Heuristic: ~5ms
- Latencia ML: ~18ms
- Latencia LLM: ~2-3s
- Accuracy ML: >95%
- Pesos finales: Heuristic 30%, ML 50%, LLM 20%

---

**Documento generado:** 15 Febrero 2026
**Proyecto:** Guard-IA - Tesis Universidad ORT Uruguay
**Cliente:** Strike Security