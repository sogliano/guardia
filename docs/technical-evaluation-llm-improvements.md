# Evaluacion Tecnica: Mejoras al Pipeline de Deteccion

**Proyecto:** Guard-IA — Tesis ORT Uruguay / Strike Security
**Fecha:** Enero 2026
**Autor:** Equipo Guard-IA

---

## 1. Estado Actual del Pipeline

El pipeline de Guard-IA opera en 3 capas secuenciales:

| Capa | Tecnologia | Latencia | Peso en score final |
|------|-----------|----------|-------------------|
| Heuristic Engine | Reglas deterministicas (auth, domain, URL, keywords) | ~5ms | 30% |
| ML Classifier | DistilBERT fine-tuned (66M params) | ~18ms | 50% |
| LLM Analyst | OpenAI GPT | 2-3s | 20% |

**Score final** = `heuristic * 0.30 + ml * 0.50 + llm * 0.20`

**Mejoras ya implementadas (v0.3):**
- Structured output: Claude tool_use + OpenAI response_format (elimina parsing JSON fragil)
- Few-shot examples: 3 ejemplos clasificados (phishing, legitimo, ambiguo) en el prompt
- Temperature 0: scoring deterministico en ambos providers

---

## 2. RAG con Indicadores de Compromiso (IOCs)

### 2.1 Concepto

Retrieval-Augmented Generation (RAG) permitiria al LLM Analyst consultar una base de conocimiento de amenazas en tiempo real antes de emitir su evaluacion. La base contendria:

- **Dominios maliciosos conocidos** (phishing kits, C2 infrastructure)
- **URLs reportadas** (PhishTank, OpenPhish, URLhaus)
- **Hashes de attachments maliciosos** (VirusTotal, MalwareBazaar)
- **Patrones de campanas activas** (subject lines, sender patterns)
- **Dominios legitimos verificados** (whitelist corporativa)

### 2.2 Arquitectura Propuesta

```
Email → Heuristic → ML → [RAG Query] → LLM Analyst
                          ↓
                    pgvector / Pinecone
                          ↑
                    Threat Intel Feeds
                    (PhishTank, URLhaus, internal)
```

**Vector store:** `pgvector` (extension PostgreSQL, ya usamos PostgreSQL) o servicio externo (Pinecone, Weaviate).

**Embedding model:** `text-embedding-3-small` (OpenAI) o `all-MiniLM-L6-v2` (local, sin costo API).

**Flujo:**
1. Extraer entidades del email (dominio, URLs, hashes de attachments)
2. Buscar top-K vectores mas cercanos en la base de IOCs
3. Inyectar contexto relevante en el prompt del LLM
4. LLM genera analisis informado por threat intelligence

### 2.3 Evaluacion

| Factor | Analisis |
|--------|---------|
| **Precision** | Alto impacto positivo. Dominios/URLs conocidos dan evidencia concreta al LLM. Reduce falsos negativos en campanas ya catalogadas. |
| **Latencia** | +50-150ms por query vectorial (pgvector local). Aceptable dentro del budget de 30s del pipeline. Con Pinecone: +100-300ms (red). |
| **Costo** | pgvector: $0 (ya tenemos PostgreSQL). Embeddings: ~$0.02/1M tokens con text-embedding-3-small. Feeds: PhishTank/URLhaus son gratuitos. |
| **Complejidad** | Media-alta. Requiere: migracion pgvector, ingestion pipeline para feeds, cron de actualizacion, embedding service. |
| **Frescura** | Critico. IOCs tienen vida util corta (horas-dias). Requiere ingestion cada 1-4 horas minimo. |
| **Limitaciones** | No detecta zero-day phishing (no esta en ningun feed). Complementa pero no reemplaza heuristics/ML. |

### 2.4 Recomendacion

**Prioridad: Media.** El mayor beneficio seria para campanas ya conocidas. Para una tesis, implementar una version basica con pgvector + PhishTank feed demuestra la arquitectura sin complejidad excesiva. No es critico para el MVP pero agrega valor academico significativo.

**Esfuerzo estimado:** Extension pgvector + ingestion basica + query en pipeline.

---

## 3. Feedback Loop (Aprendizaje Continuo)

### 3.1 Concepto

Actualmente, las revisiones de falsos positivos (FP reviews) se almacenan en la tabla `fp_review` pero no retroalimentan al modelo ML. Un feedback loop cerraria el ciclo:

```
Email → Pipeline → Veredicto → Analista revisa → FP Review
                                                      ↓
                                              Dataset etiquetado
                                                      ↓
                                              Retraining DistilBERT
                                                      ↓
                                              Modelo actualizado
```

### 3.2 Arquitectura Propuesta

**Fase 1: Recoleccion de labels**
- Cada FP review genera un par `(email_features, label)` donde label es `phishing` o `legitimate`
- Almacenar en tabla `training_samples` con campos: `email_id`, `features_json`, `label`, `source` (fp_review | seed | manual), `created_at`
- Las decisiones `confirmed_fp` → label=`legitimate`, `kept_flagged` → label=`phishing`

**Fase 2: Retraining pipeline**
- Script offline (`ml/retrain.py`) que:
  1. Exporta samples de `training_samples`
  2. Combina con dataset original de entrenamiento
  3. Fine-tune incremental de DistilBERT (2-3 epochs, learning rate bajo)
  4. Evalua en test set holdout
  5. Registra metricas en MLflow
  6. Si accuracy > threshold → promueve modelo

**Fase 3: Model serving**
- Hot-swap del modelo en runtime sin restart
- Versionado en MLflow Model Registry
- A/B testing: correr modelo viejo y nuevo en paralelo, comparar scores

### 3.3 Evaluacion

| Factor | Analisis |
|--------|---------|
| **Precision** | Alto impacto a largo plazo. El modelo se adapta a patrones especificos de la organizacion. |
| **Cold start** | Problema critico. Con <100 FP reviews, el retraining no tiene suficientes datos. Necesita ~500+ samples para impacto medible. |
| **Label quality** | Riesgo medio. Los analistas pueden equivocarse. Requiere consenso (2+ reviewers) o revision de labels antes de entrenar. |
| **Frecuencia** | Retraining mensual o quincenal es razonable. Diario no tiene sentido con volumen bajo de reviews. |
| **Concept drift** | El modelo se adapta a ataques nuevos que las reglas heuristicas no capturan. Ventaja significativa sobre reglas estaticas. |
| **Riesgo** | Model poisoning: un atacante podria manipular el pipeline enviando emails que generen FP reviews favorables. Mitigacion: validacion manual de training samples. |

### 3.4 Recomendacion

**Prioridad: Alta para el roadmap, Baja para MVP.**

El feedback loop es la mejora con mayor impacto a largo plazo, pero requiere volumen de datos que no tenemos en fase de tesis. Recomendacion:

1. **Ahora:** Implementar la tabla `training_samples` y la recoleccion automatica desde FP reviews. Es poco codigo y sienta las bases.
2. **Post-tesis:** Implementar retraining pipeline cuando haya 500+ samples.
3. **Documentar** la arquitectura completa en la tesis como trabajo futuro con diseño concreto.

---

## 4. Header Analysis Profundo

### 4.1 Estado Actual

El motor heuristico analiza 3 campos de autenticacion:
- **SPF** (Sender Policy Framework)
- **DKIM** (DomainKeys Identified Mail)
- **DMARC** (Domain-based Message Authentication)

Esto cubre la autenticacion basica pero ignora informacion valiosa presente en los headers completos del email.

### 4.2 Mejoras Propuestas

#### 4.2.1 Received Chain Analysis

Los headers `Received:` registran cada servidor por el que paso el email. Analizar esta cadena revela:

- **Hop count anomalo:** Emails legitimos de Google tienen 2-3 hops. Un phishing puede tener 5+ hops a traves de relays anonimos.
- **Geolocalizacion inconsistente:** Email "de" una empresa en USA que ruteó por servidores en Nigeria/Russia.
- **Timestamps inconsistentes:** Saltos temporales imposibles entre hops (e.g., un hop "antes" que el anterior).
- **Servidores desconocidos:** IPs sin reverse DNS o en listas de VPS baratos (OVH, DigitalOcean) usados para phishing.

```python
# Ejemplo de regla
def check_received_chain(headers: list[str]) -> list[EvidenceItem]:
    hops = parse_received_headers(headers)
    evidences = []
    if len(hops) > 5:
        evidences.append(EvidenceItem(
            severity="medium",
            description=f"Unusual hop count: {len(hops)} (expected 2-4)",
            score_impact=0.15,
        ))
    # Check for suspicious relay countries, timing gaps, etc.
    return evidences
```

#### 4.2.2 X-Header Anomaly Detection

Headers custom (`X-*`) revelan informacion del mail system:

- **X-Mailer / User-Agent:** Phishing masivo usa herramientas como `PHPMailer`, `SwiftMailer`, o versiones antiguas. Emails corporativos usan `Microsoft Outlook`, `Google Workspace`.
- **X-Originating-IP:** IP real del sender (si presente). Cross-reference con geolocalizacion del dominio.
- **X-Spam-Status / X-Spam-Score:** Si un upstream server ya lo flageo.
- **Ausencia de headers esperados:** Emails de Google siempre tienen `X-Google-DKIM-Signature`. Su ausencia en un email "de" Gmail es sospechoso.

#### 4.2.3 Message-ID Analysis

- **Formato:** Emails de Gmail usan formato `<random@mail.gmail.com>`. Un phishing que dice ser de Gmail con Message-ID `<random@unknown-server.com>` es sospechoso.
- **Dominio en Message-ID:** Deberia coincidir con el dominio del sender o su mail server.

#### 4.2.4 Content-Type y MIME Analysis

- **Mixed content:** Un email con `text/html` que contiene formularios inline (phishing de credenciales).
- **Encoding anomalo:** Base64 encoding innecesario en el body (ofuscacion).
- **Boundaries sospechosos:** Strings de boundary que revelan el mail client o herramienta de envio masivo.

### 4.3 Evaluacion

| Factor | Analisis |
|--------|---------|
| **Precision** | Alto impacto. Headers son dificiles de falsificar completamente. La cadena Received es especialmente confiable. |
| **Latencia** | Negligible (~1-2ms adicionales). Es procesamiento local de texto. |
| **Complejidad** | Media. Requiere parser de Received headers (regex complejo), base de datos de X-headers esperados por provider. |
| **False positives** | Riesgo medio. Emails reenviados o de mailing lists tienen cadenas Received largas legitimamente. Requiere excepciones. |
| **Dependencia** | Requiere que el email gateway proporcione headers completos. Google Workspace API los incluye. |
| **Integracion** | Se integra naturalmente como sub-engine adicional del motor heuristico existente. |

### 4.4 Recomendacion

**Prioridad: Alta.** Es la mejora con mejor relacion costo/beneficio:
- Latencia negligible (no impacta pre-delivery)
- No requiere infraestructura adicional
- Alta efectividad contra phishing sofisticado que pasa auth checks
- Se implementa como extension del motor heuristico existente

**Implementacion sugerida:**
1. Agregar `ReceivedChainAnalyzer` como sub-engine en `heuristics.py`
2. Parsear Received headers, extraer IPs, hostnames, timestamps
3. Evaluar hop count, geolocalizacion, timing consistency
4. Agregar `XHeaderAnalyzer` para deteccion de mailers sospechosos
5. Peso sugerido: 15% del score heuristico (redistribuir de Keyword engine)

---

## 5. Matriz Comparativa

| Mejora | Impacto en precision | Latencia adicional | Complejidad | Prioridad |
|--------|--------------------|--------------------|-------------|-----------|
| Structured output (ya implementado) | Medio (fiabilidad) | 0ms | Baja | Hecho |
| Few-shot examples (ya implementado) | Medio (consistencia) | +200ms (prompt mas largo) | Baja | Hecho |
| Temperature 0 (ya implementado) | Bajo (determinismo) | 0ms | Trivial | Hecho |
| **Header Analysis profundo** | **Alto** | **+2ms** | **Media** | **1 - Alta** |
| **Feedback Loop** | **Muy alto (largo plazo)** | **0ms (offline)** | **Media-alta** | **2 - Media** |
| **RAG con IOCs** | **Alto (campanas conocidas)** | **+100ms** | **Alta** | **3 - Media** |

---

## 6. Conclusion

Las mejoras ya implementadas (structured output, few-shot, temperature 0) resuelven los problemas inmediatos de fiabilidad y consistencia del LLM Analyst.

Para el roadmap de Guard-IA, las mejoras con mayor impacto son:

1. **Header Analysis** — implementable en corto plazo, sin dependencias externas, alto impacto en deteccion.
2. **Feedback Loop** — infraestructura critica para evolucion del sistema. Implementar recoleccion ahora, retraining cuando haya volumen.
3. **RAG con IOCs** — complemento valioso pero requiere infraestructura de ingestion. Viable como extension post-MVP.

Las tres mejoras son complementarias y no mutuamente excluyentes. La arquitectura actual del pipeline (capas secuenciales con scores ponderados) acomoda todas sin cambios estructurales mayores.
