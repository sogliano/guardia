# Monitoring — Propuesta de Tabs Adicionales

## Estado Actual
- **Tab LLM**: Implementado ✅
  - KPIs: Total calls, avg latency, tokens, error rate
  - Token usage trend (prompt vs completion)
  - Latency distribution histogram
  - Score agreement (LLM vs pipeline final)
  - Cost breakdown por modelo
  - Recent LLM analyses table

---

## Tabs Propuestos

### 1. Tab ML Monitoring

**Justificación**: El modelo DistilBERT (66M params) es crítico en el pipeline (~18ms por análisis). Monitorear su performance permite detectar model drift, evaluar calidad de predicciones, y optimizar tiempos.

**Métricas Propuestas**:

#### KPIs (4 cards)
- **Total ML Calls**: Count total, % vs previous period
- **Avg Latency**: Promedio + P95 (baseline: ~18ms)
- **Prediction Confidence**: Avg confidence score (0-1)
- **Error Rate**: Casos donde ML falló o timeout (target <1%)

#### Charts
- **Score Distribution**: Histogram de scores ML (0.0-1.0, buckets de 0.1)
- **Confidence vs Accuracy**: Scatter plot — confidence (eje X) vs agreement con final score (eje Y)
  - Permite identificar si el modelo está "confiado pero equivocado"
- **Latency Trend**: Line chart diario (últimos 30d) — detectar degradación
- **Score Agreement (ML vs Pipeline)**: Donut chart similar al LLM
  - % agree (<0.15 diff), minor diff, major divergence

#### Tabla
- **Recent ML Analyses**: Time, sender, ML score, final score, confidence, latency, status

**Datos necesarios** (ya disponibles en `Analysis` model):
- `stage = 'ml'`
- `score`, `confidence`, `execution_time_ms`
- `metadata_` puede extenderse para: model_version, feature_vector_stats

---

### 2. Tab Heuristics Monitoring

**Justificación**: Heuristics (~5ms) son la primera línea de defensa. Monitorear permite afinar reglas, detectar bypass patterns, y optimizar orden de ejecución.

**Métricas Propuestas**:

#### KPIs
- **Total Heuristic Runs**: Count total
- **Avg Latency**: Target <10ms
- **High Score Rate**: % emails con heuristic score ≥0.6 (early catches)
- **Zero Score Rate**: % emails con score 0.0 (missed by heuristics)

#### Charts
- **Top Triggered Rules**: Bar chart horizontal — top 10 reglas más activadas
  - Ejemplo: `suspicious_link_count`, `spf_fail`, `lookalike_domain`, etc.
- **Rule Effectiveness**: Heatmap — reglas (filas) vs final verdict (columnas)
  - Permite ver qué reglas correlacionan con blocks/quarantines
- **Score Distribution**: Histogram similar al ML
- **Latency by Rule**: Bar chart — latency promedio por tipo de heurística ejecutada

#### Tabla
- **Recent Heuristic Analyses**: Time, sender, heuristic score, final score, top triggered rules, latency

**Datos necesarios**:
- `Analysis.metadata_` para heuristics debería incluir:
  ```json
  {
    "triggered_rules": ["suspicious_link_count", "lookalike_domain"],
    "rule_scores": {
      "suspicious_link_count": 0.7,
      "lookalike_domain": 0.4
    },
    "execution_time_ms": 4
  }
  ```

---

### 3. Tab Pipeline Overview (Alternativa)

**Justificación**: Vista consolidada de todo el pipeline (Heuristics → ML → LLM) en un solo tab.

**Métricas Propuestas**:

#### KPIs
- **Total Pipeline Runs**: Count total casos analizados
- **Avg End-to-End Latency**: Promedio total (target <3s)
- **Stage Success Rates**: % success por stage (heuristic, ML, LLM)
- **Bypass Rate**: % emails que pasaron allowlist bypass

#### Charts
- **Stage Latency Breakdown**: Stacked bar chart — contribución de cada stage al total
- **Stage-by-Stage Flow**: Sankey diagram — flujo de casos entre stages
  - Ej: "1000 → Heuristics → 800 ML → 200 LLM → 50 blocked"
- **Error Distribution by Stage**: Pie chart — dónde fallan más los análisis
- **Pipeline Health Over Time**: Line chart multi-series (avg latency por stage, últimos 30d)

#### Tabla
- **Recent Full Analyses**: Time, sender, heuristic/ML/LLM scores, final score, total latency, verdict

**Datos necesarios**: Ya disponible via joins entre `Case` + `Analysis` (stages: heuristic, ml, llm)

---

## Recomendación

**Prioridad 1**: **Tab ML Monitoring**
- DistilBERT es core del sistema
- Ya hay datos disponibles (`Analysis.stage = 'ml'`)
- Alta utilidad para detectar model drift y optimizar

**Prioridad 2**: **Tab Heuristics Monitoring**
- Requiere extender `Analysis.metadata_` para heuristics (agregar triggered rules)
- Alta utilidad para afinar reglas y detectar bypass patterns

**Prioridad 3**: **Tab Pipeline Overview**
- Vista "big picture" útil pero menos accionable que tabs específicos
- Más complejo de implementar (requiere joins multi-stage)

---

## Implementación (si aprobás)

### Backend
- Crear métodos en `MonitoringService`:
  - `_get_ml_stats()` / `_get_heuristics_stats()` / `_get_pipeline_overview()`
- Actualizar schemas en `monitoring.py`
- Endpoint sigue siendo `GET /monitoring?tab=llm|ml|heuristics`

### Frontend
- Crear componentes en `components/monitoring/` (ML charts, heuristics charts)
- Actualizar store para manejar `activeTab`
- Tabs ya funcionales en `MonitoringView.vue` (actualmente solo LLM activo)

---

**Estimación de tiempo por tab**:
- ML: ~3-4h (backend service + frontend charts)
- Heuristics: ~4-5h (requiere metadata enrichment + charts)
- Pipeline Overview: ~5-6h (joins complejos + Sankey/flow charts)
