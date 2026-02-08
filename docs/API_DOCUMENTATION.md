# API Reference

Documentación completa de la API REST de Guard-IA. Todos los endpoints requieren autenticación mediante Clerk JWT.

---

## Base URL

| Entorno | URL |
|---------|-----|
| **Development** | `http://localhost:8000/api/v1` |
| **Staging** | `https://guardia-backend-staging-xxxxx.run.app/api/v1` |
| **Production** | `https://guardia-backend-xxxxx.run.app/api/v1` |

---

## Authentication

Todos los endpoints (excepto `/health`) requieren autenticación mediante Clerk JWT.

### Headers

```http
Authorization: Bearer <clerk-jwt-token>
Content-Type: application/json
```

### Obtener Token

El frontend obtiene el token automáticamente vía Clerk:

```typescript
import { useAuth } from '@clerk/vue'

const { getToken } = useAuth()
const token = await getToken()
```

### Roles

| Role | Permisos |
|------|----------|
| `analyst` | Ver casos, resolver casos, ver emails, acceder a dashboard |
| `administrator` | Todos los permisos de analyst + gestión de usuarios |

---

## Rate Limits

Todos los endpoints tienen rate limiting implementado con `slowapi`.

| Endpoint | Límite |
|----------|--------|
| General (default) | **100 req/min** |
| GET /cases | **60 req/min** |
| GET /emails | **60 req/min** |
| POST /cases/{id}/resolve | **10 req/min** |
| POST /cases/{id}/quarantine | **10 req/min** |
| GET /dashboard/* | **100 req/min** |

### Response Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1675432100
```

### Error Response (429)

```json
{
  "detail": "Rate limit exceeded: 60 per 1 minute"
}
```

---

## Endpoints

### Health Check

#### GET /health

Health check endpoint (no requiere auth).

**Rate limit:** None

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "timestamp": "2025-02-01T10:00:00Z"
}
```

---

## Authentication

### GET /auth/me

Obtener perfil del usuario autenticado.

**Rate limit:** 300/min

**Headers:**
```http
Authorization: Bearer <clerk-jwt>
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clerk_id": "user_2aBC123xyz",
  "email": "analyst@strike.sh",
  "role": "analyst",
  "name": "John Doe",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-02-01T10:00:00Z"
}
```

**Response 401:**
```json
{
  "detail": "Invalid or expired token"
}
```

---

## Cases

### GET /cases

Listar casos con filtros y paginación.

**Rate limit:** 60/min

**Auth:** Analyst o Administrator

**Query Parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | int | 1 | Número de página (≥1) |
| `size` | int | 20 | Items por página (1-100) |
| `status` | string | - | Filtrar por status: `pending`, `analyzing`, `quarantined`, `resolved` |
| `risk_level` | string | - | Filtrar por nivel de riesgo: `low`, `medium`, `high`, `critical` |
| `verdict` | string | - | Filtrar por veredicto: `allowed`, `warned`, `quarantined`, `blocked` |
| `date_from` | string | - | Fecha inicio (ISO 8601): `2025-01-01T00:00:00Z` |
| `date_to` | string | - | Fecha fin (ISO 8601): `2025-02-01T23:59:59Z` |
| `search` | string | - | Búsqueda en sender, recipient, subject |
| `sender` | string | - | Filtrar por remitente exacto |

**Example Request:**
```http
GET /api/v1/cases?page=1&size=20&status=quarantined&risk_level=high
Authorization: Bearer <token>
```

**Response 200:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "quarantined",
      "risk_level": "high",
      "final_score": 0.87,
      "final_verdict": "quarantined",
      "heuristics_score": 0.65,
      "ml_score": 0.92,
      "llm_score": 0.85,
      "created_at": "2025-02-01T09:30:00Z",
      "updated_at": "2025-02-01T09:30:15Z",
      "email": {
        "sender": "ceo@evil-phishing.com",
        "recipient": "user@strike.sh",
        "subject": "URGENT: Wire Transfer Required",
        "received_at": "2025-02-01T09:29:50Z"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

**Response 400:**
```json
{
  "detail": "Invalid page number"
}
```

---

### GET /cases/{case_id}

Obtener detalle de un caso específico.

**Rate limit:** 60/min

**Auth:** Analyst o Administrator

**Path Parameters:**
- `case_id` (UUID): ID del caso

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "quarantined",
  "risk_level": "high",
  "final_score": 0.87,
  "final_verdict": "quarantined",
  "heuristics_score": 0.65,
  "ml_score": 0.92,
  "llm_score": 0.85,
  "created_at": "2025-02-01T09:30:00Z",
  "updated_at": "2025-02-01T09:30:15Z",
  "email": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "sender": "ceo@evil-phishing.com",
    "recipient": "user@strike.sh",
    "subject": "URGENT: Wire Transfer Required",
    "body": "Dear employee, please process this wire transfer immediately...",
    "headers": {
      "Return-Path": "<bounce@evil.com>",
      "Received-SPF": "fail"
    },
    "received_at": "2025-02-01T09:29:50Z"
  },
  "analyses": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "stage": "heuristics",
      "score": 0.65,
      "evidences": {
        "suspicious_sender": {
          "score": 0.8,
          "reason": "Domain mismatch with display name"
        },
        "urgency_keywords": {
          "score": 0.7,
          "reason": "Contains urgent language"
        },
        "suspicious_urls": {
          "score": 0.5,
          "reason": "URL domain does not match sender"
        }
      },
      "completed_at": "2025-02-01T09:30:05Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "stage": "ml",
      "score": 0.92,
      "model_version": "distilbert-guardia-v1.2",
      "confidence": 0.94,
      "completed_at": "2025-02-01T09:30:08Z"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "stage": "llm",
      "score": 0.85,
      "explanation": "This email exhibits clear phishing characteristics: impersonation of executive, urgent wire transfer request, domain mismatch, and failed SPF check.",
      "confidence": 0.88,
      "model_used": "gpt-4o-mini",
      "completed_at": "2025-02-01T09:30:15Z"
    }
  ],
  "alert_events": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "event_type": "case_quarantined",
      "severity": "high",
      "message": "Email quarantined due to high phishing score",
      "created_at": "2025-02-01T09:30:15Z"
    }
  ]
}
```

**Response 404:**
```json
{
  "detail": "Case not found"
}
```

---

### POST /cases/{case_id}/resolve

Resolver un caso con veredicto final (analyst decision).

**Rate limit:** 10/min

**Auth:** Analyst o Administrator

**Path Parameters:**
- `case_id` (UUID): ID del caso

**Request Body:**
```json
{
  "verdict": "allowed",
  "notes": "False positive - legitimate email from verified partner"
}
```

**Fields:**
- `verdict` (string, required): `allowed`, `warned`, `quarantined`, `blocked`
- `notes` (string, optional): Notas del analista (max 500 chars)

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "final_verdict": "allowed",
  "notes": "False positive - legitimate email from verified partner",
  "resolved_by": "user_2aBC123xyz",
  "resolved_at": "2025-02-01T10:00:00Z"
}
```

**Response 400:**
```json
{
  "detail": "Invalid verdict value"
}
```

**Response 404:**
```json
{
  "detail": "Case not found"
}
```

---

### POST /cases/{case_id}/quarantine

Poner un caso en cuarentena manualmente.

**Rate limit:** 10/min

**Auth:** Analyst o Administrator

**Path Parameters:**
- `case_id` (UUID): ID del caso

**Request Body:**
```json
{
  "reason": "Suspected BEC attack based on executive impersonation"
}
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "quarantined",
  "final_verdict": "quarantined",
  "quarantined_at": "2025-02-01T10:00:00Z"
}
```

---

### POST /cases/{case_id}/release

Liberar un caso de cuarentena (envía email a destinatario).

**Rate limit:** 10/min

**Auth:** Analyst o Administrator

**Path Parameters:**
- `case_id` (UUID): ID del caso

**Request Body:**
```json
{
  "notes": "Verified as safe after manual review"
}
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "final_verdict": "allowed",
  "released_at": "2025-02-01T10:00:00Z",
  "email_delivered": true
}
```

**Response 400:**
```json
{
  "detail": "Case is not quarantined"
}
```

---

## Emails

### GET /emails

Listar emails con filtros y paginación.

**Rate limit:** 60/min

**Auth:** Analyst o Administrator

**Query Parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | int | 1 | Número de página |
| `size` | int | 20 | Items por página (1-100) |
| `sender` | string | - | Filtrar por remitente |
| `recipient` | string | - | Filtrar por destinatario |
| `date_from` | string | - | Fecha inicio (ISO 8601) |
| `date_to` | string | - | Fecha fin (ISO 8601) |
| `search` | string | - | Búsqueda en sender, recipient, subject, body |

**Response 200:**
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "sender": "partner@legitimate.com",
      "recipient": "user@strike.sh",
      "subject": "Meeting follow-up",
      "received_at": "2025-02-01T09:00:00Z",
      "has_case": true,
      "case_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total": 1000,
  "page": 1,
  "size": 20,
  "pages": 50
}
```

---

### GET /emails/{email_id}

Obtener detalle de un email específico.

**Rate limit:** 60/min

**Auth:** Analyst o Administrator

**Response 200:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "sender": "partner@legitimate.com",
  "recipient": "user@strike.sh",
  "subject": "Meeting follow-up",
  "body": "Hi, following up on our meeting yesterday...",
  "html_body": "<html><body>Hi, following up...</body></html>",
  "headers": {
    "Return-Path": "<partner@legitimate.com>",
    "Received-SPF": "pass",
    "DKIM-Signature": "v=1; a=rsa-sha256; ..."
  },
  "attachments": [
    {
      "filename": "agenda.pdf",
      "content_type": "application/pdf",
      "size_bytes": 45120
    }
  ],
  "received_at": "2025-02-01T09:00:00Z",
  "case_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Dashboard

### GET /dashboard/stats

Obtener estadísticas generales del dashboard.

**Rate limit:** 100/min

**Auth:** Analyst o Administrator

**Query Parameters:**
- `days` (int, default: 7): Período en días (1-90)

**Response 200:**
```json
{
  "period_days": 7,
  "total_emails": 1542,
  "total_cases": 892,
  "quarantined_count": 87,
  "avg_score": 0.32,
  "high_risk_count": 65,
  "pipeline_avg_duration_ms": 4820,
  "detection_rate": 0.58,
  "false_positive_rate": 0.03
}
```

---

### GET /dashboard/trends

Obtener tendencias de detecciones a lo largo del tiempo.

**Rate limit:** 100/min

**Auth:** Analyst o Administrator

**Query Parameters:**
- `days` (int, default: 7): Período en días (1-90)
- `granularity` (string, default: "day"): `hour`, `day`, `week`

**Response 200:**
```json
{
  "period_days": 7,
  "granularity": "day",
  "data": [
    {
      "date": "2025-01-26",
      "total_emails": 220,
      "quarantined": 12,
      "avg_score": 0.28
    },
    {
      "date": "2025-01-27",
      "total_emails": 205,
      "quarantined": 15,
      "avg_score": 0.35
    }
  ]
}
```

---

### GET /dashboard/top-threats

Obtener top amenazas detectadas.

**Rate limit:** 100/min

**Auth:** Analyst o Administrator

**Query Parameters:**
- `days` (int, default: 7): Período en días
- `limit` (int, default: 10): Número de resultados (1-50)

**Response 200:**
```json
{
  "period_days": 7,
  "threats": [
    {
      "sender": "phishing@evil.com",
      "count": 45,
      "avg_score": 0.89,
      "last_seen": "2025-02-01T09:30:00Z"
    },
    {
      "sender": "scam@fake-bank.com",
      "count": 32,
      "avg_score": 0.82,
      "last_seen": "2025-02-01T08:15:00Z"
    }
  ]
}
```

---

## Quarantine

### GET /quarantine

Listar casos en cuarentena.

**Rate limit:** 60/min

**Auth:** Analyst o Administrator

**Query Parameters:**
- `page` (int, default: 1)
- `size` (int, default: 20)
- `risk_level` (string): `high`, `critical`
- `date_from` (string): ISO 8601
- `date_to` (string): ISO 8601

**Response 200:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": {
        "sender": "ceo@evil.com",
        "recipient": "user@strike.sh",
        "subject": "URGENT: Wire Transfer"
      },
      "final_score": 0.87,
      "risk_level": "high",
      "quarantined_at": "2025-02-01T09:30:15Z"
    }
  ],
  "total": 87,
  "page": 1,
  "size": 20
}
```

---

## Monitoring

### GET /monitoring/pipeline-status

Obtener estado del pipeline de detección.

**Rate limit:** 100/min

**Auth:** Analyst o Administrator

**Response 200:**
```json
{
  "status": "healthy",
  "stages": {
    "heuristics": {
      "status": "healthy",
      "avg_duration_ms": 5,
      "success_rate": 0.998
    },
    "ml": {
      "status": "healthy",
      "avg_duration_ms": 18,
      "model_loaded": true,
      "model_version": "distilbert-guardia-v1.2",
      "success_rate": 0.995
    },
    "llm": {
      "status": "healthy",
      "avg_duration_ms": 2800,
      "model": "gpt-4o-mini",
      "success_rate": 0.97,
      "rate_limit_remaining": 450
    }
  },
  "total_avg_duration_ms": 4820,
  "cases_processed_last_hour": 42
}
```

---

### GET /monitoring/alerts

Obtener alertas del sistema.

**Rate limit:** 100/min

**Auth:** Administrator

**Query Parameters:**
- `severity` (string): `low`, `medium`, `high`, `critical`
- `limit` (int, default: 20)

**Response 200:**
```json
{
  "alerts": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "event_type": "pipeline_timeout",
      "severity": "medium",
      "message": "Pipeline timeout occurred for case 550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-02-01T09:45:00Z",
      "acknowledged": false
    }
  ]
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Descripción |
|------|-------------|
| **200** | Success |
| **201** | Created |
| **400** | Bad Request - Invalid parameters |
| **401** | Unauthorized - Missing or invalid auth token |
| **403** | Forbidden - Insufficient permissions |
| **404** | Not Found - Resource does not exist |
| **422** | Unprocessable Entity - Validation error |
| **429** | Too Many Requests - Rate limit exceeded |
| **500** | Internal Server Error |

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "verdict"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## OpenAPI Schema

La especificación completa de OpenAPI está disponible en:

**Development:**
```
http://localhost:8000/docs
http://localhost:8000/redoc
http://localhost:8000/openapi.json
```

**Production:**
```
https://guardia-backend-xxxxx.run.app/docs
https://guardia-backend-xxxxx.run.app/redoc
https://guardia-backend-xxxxx.run.app/openapi.json
```

---

## Code Examples

### Python (httpx)

```python
import httpx
import asyncio

async def get_cases():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/cases",
            params={"page": 1, "size": 20, "status": "quarantined"},
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

cases = asyncio.run(get_cases())
print(cases)
```

### TypeScript (Axios)

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    Authorization: `Bearer ${token}`,
  },
})

// Get cases
const { data } = await api.get('/cases', {
  params: {
    page: 1,
    size: 20,
    status: 'quarantined',
  },
})

// Resolve case
await api.post(`/cases/${caseId}/resolve`, {
  verdict: 'allowed',
  notes: 'False positive',
})
```

### cURL

```bash
# Get cases
curl -X GET "http://localhost:8000/api/v1/cases?page=1&size=20" \
  -H "Authorization: Bearer <token>"

# Resolve case
curl -X POST "http://localhost:8000/api/v1/cases/{case_id}/resolve" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"verdict": "allowed", "notes": "False positive"}'
```

---

## Changelog

### v0.2.0 (Current)
- ✅ Rate limiting en 100% endpoints
- ✅ Slowapi integration
- ✅ Clerk JWT authentication
- ✅ Complete CRUD para casos
- ✅ Dashboard endpoints
- ✅ Monitoring endpoints

### v0.1.0
- 🔧 Initial API implementation
- 🔧 Basic cases endpoints
- 🔧 Email endpoints

---

## Resources

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura completa
- [TESTING.md](./TESTING.md) - Como testear la API
- [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md) - Setup local y workflow de desarrollo
