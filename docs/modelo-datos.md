# Guard-IA - Modelo de Datos v2.0

Documento de referencia para el modelo de datos rediseñado desde cero.
Basado en: prototipos UI (14 pantallas Pencil) + Documentación Principal (tesis).

**Fecha**: Enero 2026
**Tablas totales**: 14
**Motor**: PostgreSQL 15 + SQLAlchemy async + UUID PKs

---

## Diagrama de Relaciones

```
users
  |-- case_notes (1:N)
  |-- notifications (1:N)
  |-- quarantine_actions.performed_by (1:N)
  |-- fp_reviews.reviewer_id (1:N)
  |-- cases.resolved_by (1:N)
  |-- policy_entries.added_by (1:N)
  |-- custom_rules.created_by (1:N)
  |-- alert_rules.created_by (1:N)
  |-- settings.updated_by (1:N)

emails (1:1) --- cases
                    |-- analyses (1:N, una por etapa)
                    |     |-- evidences (1:N por analisis)
                    |-- quarantine_actions (1:N, audit log)
                    |-- fp_reviews (1:N, audit log)
                    |-- case_notes (1:N)
                    |-- alert_events.case_id (N:1)

alert_rules (1:N) --- alert_events

policy_entries (standalone)
custom_rules (standalone)
settings (standalone, key-value)
```

---

## Enums y Constantes

```python
# CaseStatus - Estado del caso en el flujo de analisis
pending | analyzing | analyzed | quarantined | resolved

# RiskLevel - Nivel de riesgo evaluado (NO es la accion tomada)
low | medium | high | critical

# Verdict - Accion/veredicto del pipeline sobre el email
allowed | warned | quarantined | blocked

# PipelineStage - Etapas del pipeline de analisis
heuristic | ml | llm

# ThreatCategory - Categoria de amenaza (para reportes/analytics)
bec_impersonation | credential_phishing | malware_payload | generic_phishing | clean

# EvidenceType - Tipos de evidencia detectados
domain_spoofing | domain_typosquatting | domain_blacklisted | domain_suspicious_tld
url_shortener | url_ip_based | url_mismatch | url_suspicious
keyword_urgency | keyword_phishing | keyword_caps_abuse
auth_spf_fail | auth_dkim_fail | auth_dmarc_fail | auth_reply_to_mismatch
ml_high_score | ceo_impersonation | sender_impersonation

# Severity - Severidad generica
low | medium | high | critical

# QuarantineAction - Acciones CISO sobre emails en cuarentena
released | kept | deleted

# PolicyListType
whitelist | blacklist

# PolicyEntryType
domain | email | ip

# AlertChannel
email | slack

# AlertDeliveryStatus
pending | delivered | failed

# NotificationType
critical_threat | quarantine_pending | false_positive | pipeline_health | system

# NotificationSeverity
info | warning | critical

# FPReviewDecision
confirmed_fp | kept_flagged

# UserRole
administrator | analyst | auditor
```

**Thresholds por defecto:**
- ALLOW: score < 0.3
- WARN: 0.3 <= score < 0.6
- QUARANTINE: 0.6 <= score < 0.8
- BLOCK: score >= 0.8

**Pesos heuristicos:** domain=0.25, url=0.25, keyword=0.25, auth=0.25

---

## Tablas

### 1. users

Usuarios sincronizados desde Clerk via JIT provisioning.
Pantallas: Login, Settings > Users & Roles, sidebar footer.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| clerk_id | VARCHAR(255) | UNIQUE NOT NULL INDEX | ID externo de Clerk |
| email | VARCHAR(255) | UNIQUE NOT NULL | |
| full_name | VARCHAR(255) | NOT NULL | |
| role | VARCHAR(20) | NOT NULL DEFAULT 'analyst' | UserRole enum |
| is_active | BOOLEAN | NOT NULL DEFAULT true | |
| last_login_at | TIMESTAMPTZ | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

---

### 2. emails

Artefactos de email originales con todos los metadatos para el pipeline.
Pantallas: Case Detail (Email Content tab), Email Explorer.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| message_id | VARCHAR(998) | UNIQUE NOT NULL INDEX | RFC 5322 Message-ID |
| sender_email | VARCHAR(320) | NOT NULL INDEX | RFC 5321 max |
| sender_name | VARCHAR(255) | NULLABLE | Display name |
| reply_to | VARCHAR(320) | NULLABLE | Para deteccion de mismatch (Screen 4) |
| recipient_email | VARCHAR(320) | NOT NULL | Destinatario principal (To) |
| recipients_cc | JSONB | NOT NULL DEFAULT '[]' | Lista CC como array de strings |
| subject | TEXT | NULLABLE | |
| body_text | TEXT | NULLABLE | Cuerpo plain-text |
| body_html | TEXT | NULLABLE | Cuerpo HTML |
| headers | JSONB | NOT NULL DEFAULT '{}' | Headers crudos del email |
| urls | JSONB | NOT NULL DEFAULT '[]' | URLs extraidas [{url, display_text}] |
| attachments | JSONB | NOT NULL DEFAULT '[]' | [{filename, content_type, size_bytes}] |
| auth_results | JSONB | NOT NULL DEFAULT '{}' | {spf, dkim, dmarc} parseados |
| received_at | TIMESTAMPTZ | NULLABLE INDEX | Timestamp original del email |
| ingested_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | Cuando Guard-IA lo ingesto |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Indices adicionales: `ix_emails_sender_received` (sender_email, received_at DESC)

Cambios vs PoC:
- Renombrada de `email_artifacts` a `emails`
- Agregado `reply_to` (mismatch detection, Screen 4)
- Agregado `recipients_cc` (JSONB array)
- Agregado `auth_results` (SPF/DKIM/DMARC parseados)
- `message_id` ampliado a VARCHAR(998) per RFC 5322

---

### 3. cases

Contenedor central de analisis. Un caso por email.
Pantallas: Cases List, Case Detail, Dashboard > Recent Critical Cases.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| email_id | UUID | FK emails.id UNIQUE NOT NULL | 1:1 con email |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' INDEX | CaseStatus enum |
| final_score | FLOAT | NULLABLE | 0.0-1.0, se setea post-pipeline |
| risk_level | VARCHAR(20) | NULLABLE INDEX | RiskLevel: low/medium/high/critical |
| verdict | VARCHAR(20) | NULLABLE INDEX | Verdict: allowed/warned/quarantined/blocked |
| threat_category | VARCHAR(30) | NULLABLE | ThreatCategory, para grafico de reportes |
| pipeline_duration_ms | INTEGER | NULLABLE | Tiempo total de pipeline |
| resolved_by | UUID | FK users.id NULLABLE | Usuario que resolvio manualmente |
| resolved_at | TIMESTAMPTZ | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Indices adicionales: `ix_cases_verdict_created` (verdict, created_at DESC)

Relaciones:
- `email` (1:1 via email_id UNIQUE)
- `analyses` (1:N)
- `quarantine_actions` (1:N)
- `fp_reviews` (1:N)
- `notes` (1:N)
- `resolver` (FK users)

Cambios vs PoC:
- `action` renombrado a `verdict` (semantica clara)
- `risk_level` ahora es low/medium/high/critical (NO allow/warn/quarantine/block)
- Agregado `threat_category` para Screen 9 pie chart
- Agregado `pipeline_duration_ms` para KPI "Avg Response Time"
- `email_artifact_id` renombrado a `email_id`

---

### 4. analyses

Resultado de cada etapa del pipeline. Una por stage por caso.
Pantallas: Case Detail > Pipeline Analysis tab, Risk Score Breakdown.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| case_id | UUID | FK cases.id NOT NULL INDEX | |
| stage | VARCHAR(20) | NOT NULL | PipelineStage enum |
| score | FLOAT | NULLABLE | 0.0-1.0 |
| confidence | FLOAT | NULLABLE | Score de confianza ML |
| explanation | TEXT | NULLABLE | Explicacion generada por LLM |
| metadata | JSONB | NOT NULL DEFAULT '{}' | Detalles especificos de la etapa |
| execution_time_ms | INTEGER | NULLABLE | Tiempo de ejecucion de la etapa |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Constraint: UNIQUE (case_id, stage) - cada etapa se ejecuta una vez por caso.

Relaciones:
- `case` (N:1)
- `evidences` (1:N)

Cambios vs PoC:
- Renombrada de `decisions` a `analyses` (alineado con PDF)
- Agregados `confidence` y `explanation` como columnas explicitas
- Eliminado `FINAL` de PipelineStage (el score final esta en `cases.final_score`)
- Unique constraint (case_id, stage)
- Write-once: sin `updated_at`

---

### 5. evidences

Senales de deteccion individuales producidas por el motor heuristico.
Pantallas: Case Detail > Evidences tab, "Top Evidences" en AI Analysis Summary.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| analysis_id | UUID | FK analyses.id NOT NULL INDEX | Antes `decision_id` |
| type | VARCHAR(50) | NOT NULL INDEX | EvidenceType enum |
| severity | VARCHAR(20) | NOT NULL | Severity enum |
| description | TEXT | NOT NULL | Descripcion legible |
| raw_data | JSONB | NOT NULL DEFAULT '{}' | Datos de deteccion crudos |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Cambios vs PoC: FK renombrada de `decision_id` a `analysis_id`. Write-once, sin `updated_at`.

---

### 6. quarantine_actions (NUEVA)

Acciones CISO sobre emails en cuarentena. Audit trail.
Pantallas: Quarantine Management (botones Release/Keep/Delete).
PDF: Secuencia CISO approve/reject.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| case_id | UUID | FK cases.id NOT NULL INDEX | Caso en cuarentena |
| action | VARCHAR(20) | NOT NULL | QuarantineAction enum |
| reason | TEXT | NULLABLE | Razon del CISO |
| performed_by | UUID | FK users.id NOT NULL | CISO que ejecuto |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |

Inmutable (audit trail). Sin `updated_at`.

---

### 7. fp_reviews (NUEVA)

Decisiones de revision de falsos positivos.
Pantallas: False Positive Review (Screen 11).
PDF: RF5 - gestion de excepciones.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| case_id | UUID | FK cases.id NOT NULL INDEX | Caso bajo revision |
| decision | VARCHAR(20) | NOT NULL | FPReviewDecision enum |
| reviewer_id | UUID | FK users.id NOT NULL | Analista que reviso |
| notes | TEXT | NULLABLE | Notas del reviewer (textarea en Screen 11) |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |

Inmutable (audit trail). Multiples reviews por caso permitidas (re-flagging).

---

### 8. case_notes (NUEVA)

Notas de texto libre en casos.
Pantallas: Case Detail > Notes tab, boton "Add Note".

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| case_id | UUID | FK cases.id NOT NULL INDEX | |
| author_id | UUID | FK users.id NOT NULL | |
| content | TEXT | NOT NULL | Contenido de la nota |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |

Append-only. Sin `updated_at`.

---

### 9. policy_entries (NUEVA, reemplaza `policies`)

Entradas de whitelist y blacklist con columnas explicitas.
Pantallas: Policies > Whitelist tab, Blacklist tab.
PDF: RF6 - administracion de listas blancas/negras.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| list_type | VARCHAR(20) | NOT NULL INDEX | PolicyListType: whitelist/blacklist |
| entry_type | VARCHAR(20) | NOT NULL | PolicyEntryType: domain/email/ip |
| value | VARCHAR(320) | NOT NULL INDEX | El dominio/email/IP real |
| is_active | BOOLEAN | NOT NULL DEFAULT true | Toggle activo/inactivo |
| added_by | UUID | FK users.id NULLABLE | Usuario que agrego |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Constraint: UNIQUE (list_type, entry_type, value) - sin duplicados.

Cambios vs PoC: Reemplaza `policies` (JSONB generico) con columnas tipadas.

---

### 10. custom_rules (NUEVA)

Reglas de deteccion personalizadas.
Pantallas: Policies > Custom Rules tab.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Nombre de la regla |
| description | TEXT | NULLABLE | |
| conditions | JSONB | NOT NULL | Condiciones (estructura flexible) |
| action | VARCHAR(20) | NOT NULL | Accion cuando matchea: warn/block/quarantine |
| is_active | BOOLEAN | NOT NULL DEFAULT true | |
| created_by | UUID | FK users.id NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

JSONB para `conditions` es apropiado aqui porque las reglas custom tienen logica variable.

---

### 11. alert_rules (NUEVA, reemplaza `alerts`)

Definiciones de reglas de alerta configurables.
Pantallas: Alerts Management > Alert Rule Cards (toggle on/off, thresholds, channels).

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Ej: "Critical Threat Detected" |
| description | TEXT | NULLABLE | |
| severity | VARCHAR(20) | NOT NULL | Severity enum |
| conditions | JSONB | NOT NULL | Condiciones de trigger |
| channels | JSONB | NOT NULL DEFAULT '[]' | [{channel, target}] |
| is_active | BOOLEAN | NOT NULL DEFAULT true INDEX | Toggle |
| created_by | UUID | FK users.id NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

---

### 12. alert_events (NUEVA)

Instancias de alertas disparadas (historial).
Pantallas: Alerts Management > Alert History table.

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| alert_rule_id | UUID | FK alert_rules.id NOT NULL INDEX | Regla que disparo |
| case_id | UUID | FK cases.id NULLABLE INDEX | Caso relacionado |
| severity | VARCHAR(20) | NOT NULL | Severidad al momento del trigger |
| channel | VARCHAR(20) | NOT NULL | AlertChannel enum |
| delivery_status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | AlertDeliveryStatus |
| trigger_info | JSONB | NOT NULL DEFAULT '{}' | Contexto del trigger |
| delivered_at | TIMESTAMPTZ | NULLABLE | Cuando se envio |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |

---

### 13. notifications

Feed de notificaciones in-app por usuario.
Pantallas: Notification Center (drawer lateral).

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK users.id NOT NULL INDEX | Usuario destino |
| type | VARCHAR(30) | NOT NULL INDEX | NotificationType enum |
| severity | VARCHAR(20) | NOT NULL | NotificationSeverity enum |
| title | VARCHAR(255) | NOT NULL | |
| message | TEXT | NULLABLE | |
| reference_id | UUID | NULLABLE | FK polimorfica a case/alert |
| reference_type | VARCHAR(30) | NULLABLE | "case", "alert_event", etc. |
| is_read | BOOLEAN | NOT NULL DEFAULT false INDEX | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() INDEX | |

Indice compuesto: `ix_notifications_user_unread` (user_id, is_read, created_at DESC)

Cambios vs PoC:
- Agregado `severity` (tabs de filtro: All/Critical/Alerts/System)
- Agregado `reference_id` + `reference_type` (navegacion al recurso)
- Eliminado `metadata` JSONB (reemplazado por reference fields)

---

### 14. settings (NUEVA)

Configuracion de la aplicacion persistida en BD (key-value).
Pantallas: Settings (General, Pipeline Config, Data Retention).

| Columna | Tipo | Constraints | Notas |
|---------|------|-------------|-------|
| id | UUID | PK | |
| key | VARCHAR(100) | UNIQUE NOT NULL INDEX | Clave del setting |
| value | JSONB | NOT NULL | Valor (tipo flexible) |
| updated_by | UUID | FK users.id NULLABLE | Ultimo usuario que modifico |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

Settings iniciales (seed):
```
org_name                     -> "Strike Security"
org_industry                 -> "Cybersecurity"
org_admin_email              -> "admin@strikesecurity.com"
org_timezone                 -> "America/Montevideo"
pipeline_heuristic_enabled   -> true
pipeline_heuristic_threshold -> 0.3
pipeline_ml_enabled          -> true
pipeline_ml_threshold        -> 0.6
pipeline_llm_enabled         -> true
pipeline_llm_threshold       -> 0.8
threshold_allow              -> 0.3
threshold_warn               -> 0.6
threshold_quarantine         -> 0.8
data_retention_days          -> 365
notification_email_enabled   -> true
```

---

## Resumen de Crecimiento de Datos

| # | Tabla | Crecimiento | Proposito |
|---|-------|-------------|-----------|
| 1 | users | Bajo (invitacion) | Auth, audit |
| 2 | emails | Alto (100K/dia target) | Almacenamiento de emails |
| 3 | cases | Alto (1:1 con emails) | Contenedor de analisis |
| 4 | analyses | Alto (3 por caso) | Resultados por etapa |
| 5 | evidences | Alto (N por analisis) | Senales de deteccion |
| 6 | quarantine_actions | Bajo-medio | Audit CISO |
| 7 | fp_reviews | Bajo | Audit FP |
| 8 | case_notes | Bajo | Notas de analistas |
| 9 | policy_entries | Bajo | Whitelist/blacklist |
| 10 | custom_rules | Bajo | Reglas personalizadas |
| 11 | alert_rules | Bajo | Config de alertas |
| 12 | alert_events | Medio | Historial de alertas |
| 13 | notifications | Medio | Feed in-app |
| 14 | settings | Estatico (~15 rows) | Configuracion |

---

## Mapeo Pantallas -> Tablas

| Pantalla | Tablas que usa |
|----------|---------------|
| Login (Screen 1) | users |
| Dashboard (Screen 2) | cases, emails, analyses, alert_events |
| Cases List (Screen 3) | cases, emails |
| Case Detail (Screen 4) | cases, emails, analyses, evidences, case_notes |
| Quarantine (Screen 5) | cases, emails, quarantine_actions |
| Email Explorer (Screen 6) | emails, cases |
| Policies (Screen 7) | policy_entries, custom_rules |
| Alerts (Screen 8) | alert_rules, alert_events, cases |
| Reports (Screen 9) | cases, emails, fp_reviews |
| Settings (Screen 10) | settings, users |
| FP Review (Screen 11) | cases, emails, analyses, fp_reviews |
| Notifications (Screen 12) | notifications |
