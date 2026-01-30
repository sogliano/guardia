# RAG con Indicadores de Compromiso (IOCs) — Documento de Implementacion

**Proyecto:** Guard-IA — Tesis ORT Uruguay / Strike Security
**Fecha:** Enero 2026

---

## 1. Que es RAG

**Retrieval-Augmented Generation (RAG)** es un patron de arquitectura que combina un modelo de lenguaje (LLM) con una base de conocimiento externa consultable en tiempo real. En lugar de depender unicamente del conocimiento interno del modelo (entrenado con datos estaticos), RAG permite inyectar informacion actualizada y especifica del dominio en el prompt del LLM antes de que genere su respuesta.

### Flujo basico:

```
Consulta del usuario → Busqueda en base de conocimiento → Contexto relevante → LLM genera respuesta informada
```

En el contexto de Guard-IA, RAG permitiria al LLM Analyst consultar una base de **Indicadores de Compromiso (IOCs)** — dominios maliciosos, URLs de phishing, patrones de campanas activas — antes de emitir su evaluacion de riesgo.

---

## 2. Que son los IOCs

Los **Indicators of Compromise** son artefactos observables que indican actividad maliciosa:

| Tipo de IOC | Ejemplo | Fuente tipica |
|-------------|---------|---------------|
| Dominio malicioso | `paypa1-security.com` | PhishTank, interno |
| URL de phishing | `https://bit.ly/3xFake` | URLhaus, OpenPhish |
| Hash de archivo | `a1b2c3...` (SHA-256 de malware) | VirusTotal, MalwareBazaar |
| IP de C2 | `185.220.101.x` | Abuse.ch, AlienVault OTX |
| Patron de subject | `"Urgent: Account Suspended"` | Campanas detectadas internamente |
| Sender pattern | `security@*-verify.io` | Deteccion interna |

### Fuentes de IOCs (gratuitas)

- **PhishTank** (phishtank.org): Base colaborativa de URLs de phishing verificadas. API gratuita.
- **URLhaus** (urlhaus.abuse.ch): URLs distribuidas para malware. Datos abiertos, actualizado cada 5 min.
- **OpenPhish** (openphish.com): Feed de URLs de phishing. Version gratuita con datos limitados.
- **AlienVault OTX** (otx.alienvault.com): Plataforma de threat intelligence con API REST.
- **Abuse.ch** (abuse.ch): Feeds de malware, botnets, IPs maliciosas.

---

## 3. Arquitectura Propuesta

### 3.1 Diagrama de flujo

```
Email entrante
    │
    ▼
┌──────────────┐
│  Heuristic   │ ← Ya implementado (Layer 1)
│   Engine     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  ML Classifier│ ← Ya implementado (Layer 2)
│  DistilBERT  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│         RAG Query (nuevo)            │
│                                      │
│  1. Extraer entidades del email:     │
│     - Sender domain                  │
│     - URLs                           │
│     - Attachment hashes              │
│     - Subject patterns               │
│                                      │
│  2. Buscar en vector store:          │
│     SELECT * FROM iocs               │
│     WHERE embedding <-> query_emb    │
│     ORDER BY distance LIMIT 5        │
│                                      │
│  3. Formatear contexto relevante     │
└──────┬───────────────────────────────┘
       │ Contexto IOC
       ▼
┌──────────────┐
│  LLM Analyst │ ← Ya implementado (Layer 3)
│  OpenAI GPT  │   Ahora recibe contexto RAG
└──────────────┘
```

### 3.2 Stack tecnologico

| Componente | Tecnologia | Justificacion |
|-----------|-----------|---------------|
| **Vector store** | pgvector (extension PostgreSQL) | Ya usamos PostgreSQL. Sin infraestructura adicional. |
| **Embedding model** | `all-MiniLM-L6-v2` (sentence-transformers) | Local, sin costo API, 80MB, ~5ms/query |
| **Alternativa embedding** | `text-embedding-3-small` (OpenAI) | Mejor calidad, pero costo API (~$0.02/1M tokens) |
| **Ingestion** | Cron job / celery beat | Actualiza IOCs cada 4 horas |
| **Base de datos** | Tabla `iocs` en PostgreSQL existente | Misma DB, misma conexion |

### 3.3 Porque pgvector y no Pinecone/Weaviate

- **No requiere infraestructura adicional**: pgvector es una extension de PostgreSQL que ya usamos.
- **Misma conexion**: usa SQLAlchemy async, misma session del pipeline.
- **Costo**: $0 adicional.
- **Latencia**: ~5-15ms por query con indice HNSW. Aceptable en pipeline de 30s.
- **Limitaciones**: menos features que Pinecone (no metadata filtering nativo, menos optimizado para >1M vectores). Pero para ~100K IOCs es mas que suficiente.

---

## 4. Modelo de Datos

### 4.1 Tabla `iocs`

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE iocs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,        -- 'domain', 'url', 'hash', 'ip', 'pattern'
    value TEXT NOT NULL,               -- El IOC en si: 'paypa1-security.com'
    source VARCHAR(100) NOT NULL,      -- 'phishtank', 'urlhaus', 'internal', etc.
    severity VARCHAR(20) NOT NULL,     -- 'low', 'medium', 'high', 'critical'
    description TEXT,                  -- Descripcion legible
    tags TEXT[],                       -- ['phishing', 'credential-theft', 'paypal']
    embedding vector(384),             -- Vector embedding (384 dims for MiniLM)
    first_seen TIMESTAMP NOT NULL DEFAULT now(),
    last_seen TIMESTAMP NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE(type, value)
);

-- HNSW index for fast similarity search
CREATE INDEX idx_iocs_embedding ON iocs
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Regular indexes
CREATE INDEX idx_iocs_type ON iocs (type);
CREATE INDEX idx_iocs_active ON iocs (is_active) WHERE is_active = true;
CREATE INDEX idx_iocs_source ON iocs (source);
```

### 4.2 SQLAlchemy Model

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class IOC(Base):
    __tablename__ = "iocs"

    id = Column(UUID, primary_key=True, server_default="gen_random_uuid()")
    type = Column(String(50), nullable=False)          # domain, url, hash, ip, pattern
    value = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))
    embedding = Column(Vector(384))                     # pgvector
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
```

---

## 5. Pipeline de Ingestion

### 5.1 Flujo

```
Cron (cada 4h)
    │
    ▼
┌────────────────────┐
│  Fetch IOC feeds   │
│  - PhishTank API   │
│  - URLhaus CSV     │
│  - Internal rules  │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Deduplicar        │
│  (UPSERT by        │
│   type + value)    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Generar embeddings│
│  (MiniLM local)    │
│  Batch de 256      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  INSERT/UPDATE     │
│  en tabla iocs     │
└────────────────────┘
```

### 5.2 Script de ingestion (pseudocodigo)

```python
# backend/app/services/ioc_ingestion.py

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

async def ingest_phishtank(db: AsyncSession):
    """Fetch PhishTank verified phishing URLs."""
    response = await httpx.get(
        "http://data.phishtank.com/data/online-valid.json.gz",
        headers={"User-Agent": "guardia/1.0"},
    )
    entries = decompress_and_parse(response.content)

    for batch in chunked(entries, 256):
        texts = [f"phishing url: {e['url']} target: {e.get('target', '')}" for e in batch]
        embeddings = model.encode(texts)

        for entry, emb in zip(batch, embeddings):
            await upsert_ioc(db, IOC(
                type="url",
                value=entry["url"],
                source="phishtank",
                severity="high",
                description=f"Verified phishing URL targeting {entry.get('target', 'unknown')}",
                tags=["phishing", entry.get("target", "").lower()],
                embedding=emb.tolist(),
            ))

async def ingest_urlhaus(db: AsyncSession):
    """Fetch URLhaus malware distribution URLs."""
    # Similar: fetch CSV, parse, embed, upsert
    ...

async def run_ingestion():
    """Main ingestion entry point (called by cron)."""
    async with get_session() as db:
        await ingest_phishtank(db)
        await ingest_urlhaus(db)
        await expire_old_iocs(db, max_age_days=30)
        await db.commit()
```

### 5.3 Frecuencia de actualizacion

| Feed | Frecuencia | Volumen estimado |
|------|-----------|-----------------|
| PhishTank | Cada 4 horas | ~15,000 URLs activas |
| URLhaus | Cada 4 horas | ~30,000 URLs |
| IOCs internos | Manual / por evento | ~100-500 |

**Total estimado**: ~50,000 IOCs activos. pgvector maneja esto sin problemas.

---

## 6. Query en el Pipeline

### 6.1 RAG Query Service

```python
# backend/app/services/pipeline/rag_query.py

from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

model = SentenceTransformer("all-MiniLM-L6-v2")

async def query_iocs(
    db: AsyncSession,
    email_data: dict,
    top_k: int = 5,
) -> list[dict]:
    """Search IOC database for matches related to this email."""

    # Build query text from email entities
    parts = []
    sender = email_data.get("sender_email", "")
    if sender and "@" in sender:
        domain = sender.rsplit("@", 1)[1]
        parts.append(f"sender domain: {domain}")

    for url in email_data.get("urls", [])[:5]:
        parts.append(f"url: {url}")

    subject = email_data.get("subject", "")
    if subject:
        parts.append(f"subject: {subject}")

    if not parts:
        return []

    query_text = " | ".join(parts)
    query_embedding = model.encode(query_text).tolist()

    # Vector similarity search
    result = await db.execute(
        text("""
            SELECT type, value, source, severity, description, tags,
                   1 - (embedding <=> :emb::vector) AS similarity
            FROM iocs
            WHERE is_active = true
            AND 1 - (embedding <=> :emb::vector) > 0.5
            ORDER BY embedding <=> :emb::vector
            LIMIT :k
        """),
        {"emb": str(query_embedding), "k": top_k},
    )

    return [dict(row._mapping) for row in result.fetchall()]


def format_ioc_context(matches: list[dict]) -> str:
    """Format IOC matches as context for the LLM prompt."""
    if not matches:
        return ""

    lines = ["## Threat Intelligence (IOC Database)"]
    for m in matches:
        sim = m.get("similarity", 0)
        lines.append(
            f"- [{m['severity'].upper()}] {m['type']}: {m['value']} "
            f"(source: {m['source']}, similarity: {sim:.2f})"
        )
        if m.get("description"):
            lines.append(f"  {m['description']}")

    return "\n".join(lines)
```

### 6.2 Integracion en LLM Explainer

La integracion seria minima — agregar el contexto IOC al user_prompt:

```python
# En llm_explainer.py, metodo _build_user_prompt:

def _build_user_prompt(
    email_data: dict,
    heuristic_evidences: list[EvidenceItem],
    heuristic_score: float,
    ml_score: float,
    ml_confidence: float,
    ml_available: bool,
    ioc_context: str = "",       # <-- NUEVO parametro
) -> str:
    ...
    # Agregar contexto IOC antes del Task
    if ioc_context:
        parts.append(f"\n{ioc_context}")

    parts.append(
        "\n## Task\n"
        "Based on all evidence above (including threat intelligence if available), "
        "provide your independent risk assessment."
    )
    return "\n".join(parts)
```

### 6.3 Integracion en Orchestrator

```python
# En orchestrator.py, metodo analyze:

# Despues de heuristic + ML, antes de LLM:
from app.services.pipeline.rag_query import query_iocs, format_ioc_context

ioc_matches = await query_iocs(self.db, email_data)
ioc_context = format_ioc_context(ioc_matches)

# Pasar al LLM explainer
llm_result = await self.llm.explain(
    email_data=email_data,
    ...,
    ioc_context=ioc_context,  # <-- NUEVO
)
```

---

## 7. Impacto en Performance

| Operacion | Latencia estimada | Notas |
|-----------|------------------|-------|
| Embedding query (MiniLM local) | ~5ms | CPU, batch=1 |
| pgvector similarity search (HNSW, 50K rows) | ~10-15ms | Con indice HNSW |
| **Total RAG overhead** | **~15-20ms** | Negligible vs LLM (2-3s) |

El overhead de RAG es <1% del tiempo total del pipeline. No impacta la ventana de pre-delivery.

---

## 8. Dependencias Nuevas

```toml
# backend/pyproject.toml (nuevas)
"pgvector>=0.3.0",               # PostgreSQL vector extension bindings
"sentence-transformers>=3.0.0",  # Local embedding model (MiniLM)
```

**Nota**: `sentence-transformers` trae `torch` como dependencia, que ya tenemos instalado para DistilBERT.

---

## 9. Migracion de Base de Datos

```bash
# 1. Habilitar pgvector en PostgreSQL
# (Neon ya lo soporta nativamente, local requiere: CREATE EXTENSION vector)

# 2. Crear migracion
cd backend
alembic revision --autogenerate -m "add_iocs_table_pgvector"
alembic upgrade head
```

---

## 10. Limitaciones y Consideraciones

### Lo que RAG resuelve bien:
- Detectar dominios/URLs ya conocidos como maliciosos
- Correlacionar patrones de campanas activas
- Enriquecer el analisis LLM con evidencia concreta
- Reducir falsos negativos en amenazas catalogadas

### Lo que RAG NO resuelve:
- **Zero-day phishing**: Si el dominio/URL no esta en ningun feed, RAG no lo detecta. Para eso dependemos de heuristics + ML.
- **Ataques dirigidos (spear-phishing)**: Emails unicos, sin indicadores conocidos. El LLM y las heuristicas son mas utiles aqui.
- **Frescura de datos**: Los IOCs tienen vida util corta (horas-dias). Requiere ingestion frecuente.

### Riesgos:
- **Embedding drift**: Si cambiamos de modelo de embedding, hay que re-embedear toda la base.
- **Volumen**: Con >1M IOCs, pgvector puede volverse lento. Pero para ~50K es optimo.
- **API rate limits**: PhishTank limita a 1 request/5min en plan gratuito.

---

## 11. Plan de Implementacion

1. **Habilitar pgvector** en PostgreSQL (Neon ya lo soporta)
2. **Crear tabla `iocs`** via migracion Alembic
3. **Implementar ingestion** para PhishTank + URLhaus
4. **Implementar `rag_query.py`** con embedding local (MiniLM)
5. **Integrar en orchestrator** (pasar contexto IOC al LLM)
6. **Actualizar prompt** del LLM para usar contexto de threat intelligence
7. **Configurar cron** para ingestion cada 4 horas
8. **Testing**: verificar que IOCs conocidos mejoran la deteccion

---

## 12. Conclusion

RAG con IOCs es una mejora de alto valor que complementa las capas existentes del pipeline. Su principal ventaja es convertir al LLM Analyst de un evaluador "general" a uno informado por threat intelligence actualizada. La arquitectura con pgvector mantiene la simplicidad del stack (todo en PostgreSQL) y el overhead de latencia (~20ms) es negligible.

Es especialmente valioso como mejora post-MVP y aporta contenido academico significativo para la tesis, demostrando integracion de tecnicas de NLP (embeddings) con seguridad informatica (threat intelligence feeds).
