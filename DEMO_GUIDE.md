# Guard-IA - Guia de Demo (10 min, staging)

## Datos clave (para mencionar en cualquier momento)

- **65 emails** analizados en los ultimos 7 dias
- **17 amenazas** detectadas (26% del trafico)
- **12 bloqueados**, **5 en cuarentena**, **13 warnings**, **35 allowed**
- **Latencia promedio**: 4.5s end-to-end (incluye LLM)
- **3 capas**: Heuristicas (~44ms) + ML DistilBERT (~310ms) + LLM GPT-4o-mini (~4.3s)
- Score promedio de amenazas: **0.83**

---

## 0:00-1:30 - Dashboard (vision general)

**Que mostrar**: Pantalla principal del dashboard

**Que decir**:

> "Guard-IA es un middleware de deteccion de fraude por email que se posiciona entre internet y el inbox del usuario. Intercepta cada email **antes** de que llegue, lo analiza con 3 capas de inteligencia, y decide si dejarlo pasar, advertir, poner en cuarentena, o bloquearlo."

> "Aca vemos el dashboard de la ultima semana. Procesamos 65 emails, de los cuales 17 fueron detectados como amenazas - 12 bloqueados automaticamente y 5 puestos en cuarentena para revision manual."

**Que resaltar**:

- Los KPIs de arriba (emails, amenazas, blocked, quarantined)
- Que es **pre-delivery** - no es un scanner post-hoc
- El grafico de tendencia muestra actividad diaria

---

## 1:30-3:00 - Dashboard graficos

**Que mostrar**: Graficos de distribucion de riesgo, tendencia semanal

**Que decir**:

> "La distribucion muestra que la mayoria del trafico es legitimo - newsletters, notificaciones de GitHub, facturas de Vercel, Neon, OpenAI. Pero hay un porcentaje significativo de amenazas que el sistema detecta automaticamente."

**Que resaltar**:

- Mix realista: no todo es phishing, la mayoria es trafico legit
- Los picos de amenazas (Feb 8-9 tuvieron mas ataques)
- El sistema es **fail-open**: si crashea, el email se entrega igual (no bloquea comunicacion legitima)

---

## 3:00-5:30 - Cases (analisis detallado)

**Que mostrar**: Lista de cases -> abrir casos interesantes

### Caso estrella: Phishing - Case #42 (FedEx fake, score 0.92)

> "Este es un caso clasico de phishing. Alguien se hizo pasar por FedEx usando el dominio `fedex-tracking.xyz`. Las 3 capas coincidieron:"

- **Heuristicas** (44ms): detectaron auth failure triple (SPF, DKIM, DMARC todos fail) y el dominio sospechoso. Score: 0.77
- **ML DistilBERT** (42ms): el modelo de lenguaje detecto patrones de phishing en el texto. Score: 0.998 con 99.8% de confianza
- **LLM GPT-4o-mini** (4s): genero una explicacion en lenguaje natural de por que es phishing, mencionando la urgencia, el dominio lookalike, y los auth failures. Score: 0.92
- Score final: 0.92 -> **bloqueado automaticamente**

### Caso estrella: BEC - Case #49 (Wire transfer, score 0.90)

> "Este es mas sutil - un ataque BEC. El atacante uso `str1ke.sh` (con un '1' en vez de 'i') haciendose pasar por Martin Rodriguez, pidiendo una transferencia urgente de $15,000."

- SPF paso - el atacante realmente controla ese dominio
- Pero DKIM fallo y no hay DMARC
- Las heuristicas detectaron el **dominio lookalike** y las **keywords de urgencia**
- El ML le dio 0.999 - casi certeza absoluta
- La explicacion del LLM lo identifica como BEC y menciona especificamente la tactica de evitar llamadas telefonicas

### Otros casos BEC destacados

| Case | Sender | Subject | Score | Verdict |
|------|--------|---------|-------|---------|
| #50 | ceo@str1ke.sh | Confidential - Acquisition payment | 0.86 | blocked |
| #51 | accounting@str1ke.sh | Updated bank details - Vendor payment redirect | 0.89 | blocked |
| #52 | lucia.fernandez@str1ke.sh | Can you help me with something? (gift cards) | 0.86 | blocked |
| #53 | admin@strlke.sh | Password reset required - Security compliance | 0.78 | quarantined |

### Contraste con caso legitimo

> "En contraste, este email interno de Martin Rodriguez paso por la allowlist: dominio conocido (strike.sh) con auth valido. Bypass directo, sin gastar recursos de ML ni LLM."

---

## 5:30-8:00 - Demo en vivo

### Preparacion

Abrir Gmail personal -> componer email a **nico@guardia-sec.com**

### Email a enviar

**De**: tu Gmail personal

**Para**: nico@guardia-sec.com

**Asunto**: `Urgent: Verify your Google Workspace account`

**Cuerpo**:
```
Dear User,

Your Google Workspace account (nico@guardia-sec.com) will be deactivated
in 24 hours due to a security policy violation.

To prevent account deactivation, verify your identity immediately:
https://workspace-verify-secure.com/verify?user=nico

If you do not complete verification, you will lose access to:
- Email
- Google Drive files
- Calendar

Google Workspace Security Team
```

### Flujo

1. Enviar el email desde Gmail
2. Volver al dashboard de Guard-IA
3. Esperar ~30-60 segundos

### Que decir mientras esperas

> "Acabo de enviar un email de phishing simulado. El email llega a nuestro SMTP gateway en la VM de Google Cloud, que lo intercepta antes de entregarlo al inbox."

> "El pipeline va a correr las 3 capas: primero heuristicas en milisegundos, despues el modelo ML, y finalmente el LLM que genera la explicacion. Todo en menos de 6 segundos."

### Cuando aparezca el case

> "Ahi esta - el sistema lo detecto automaticamente. Podemos ver el score, el verdict, y la explicacion completa del LLM de por que es phishing."

---

## 8:00-9:00 - Monitoring

**Que mostrar**: Pagina de monitoring/metricas

**Que decir**:

> "El sistema de monitoring trackea la performance del pipeline en tiempo real."

- Heuristicas: promedio 44ms - es lo mas rapido
- ML DistilBERT: promedio 310ms incluyendo carga del modelo
- LLM: promedio 4.3 segundos - es el cuello de botella, pero aporta la explicabilidad
- End-to-end: 4.5 segundos promedio, bien dentro del budget de 30 segundos

**Que resaltar**:

- La latencia esta dentro de lo aceptable para pre-delivery
- El tradeoff entre velocidad y explicabilidad (heuristicas son rapidas pero no explican, LLM es lento pero genera explicaciones)
- Si el LLM falla, el sistema sigue funcionando con las otras 2 capas

---

## 9:00-10:00 - Cierre

**Puntos clave**:

1. **Pre-delivery, no post-hoc**: interceptamos antes de que llegue al inbox
2. **3 capas complementarias**: heuristicas (rapido), ML (preciso), LLM (explicable)
3. **Fail-open**: si algo falla, el email se entrega - no bloqueamos comunicacion legitima
4. **Sub-6 segundos** end-to-end en condiciones normales
5. **Deteccion de BEC**: no solo phishing obvio, sino ataques sofisticados con dominios lookalike
6. **Score ponderado con floor/cap del LLM**: el LLM no solo explica, sino que ajusta el score final
7. **Single-tenant para Google Workspace**: integrado como SMTP relay

---

## Respuestas a preguntas frecuentes

**"Y si hay falsos positivos?"**
> Hay un caso interesante: el Dependabot alert de GitHub (#24) fue quarantined con score 0.68. Es un edge case - el contenido habla de vulnerabilidades y usa lenguaje urgente. Esto muestra el tradeoff precision/recall. Un analista puede revisar y marcar como falso positivo.

**"Que modelo ML usan?"**
> DistilBERT fine-tuned, 66 millones de parametros, F1 score de 0.94. Entrenado con dataset propio de emails phishing y legitimos. Es una version compacta de BERT que mantiene 97% de la performance con la mitad de los parametros.

**"Cuanto cuesta operar esto?"**
> GPT-4o-mini cuesta aproximadamente $0.004 por email analizado. Para un volumen de 3000 emails mensuales son unos $12/mes de LLM. La infra es un Cloud Run (backend), una VM e2-micro (SMTP gateway), Neon free tier (DB), y Vercel (frontend).

**"Que pasa si el LLM no responde?"**
> El pipeline tiene un timeout de 30 segundos. Si el LLM falla o tarda demasiado, el score final se calcula solo con heuristicas (40%) y ML (60%). El email no se pierde nunca - fail-open.

**"Como manejan emails internos?"**
> Tenemos una allowlist de dominios confiables. Si el email viene de strike.sh con SPF valido, se hace bypass directo sin pasar por ML ni LLM. Eso ahorra latencia y evita falsos positivos en trafico interno.

**"Por que pre-delivery y no post-delivery?"**
> Post-delivery ya llego al inbox - el usuario ya lo puede abrir. Pre-delivery nos da la oportunidad de bloquearlo o ponerlo en cuarentena antes de que el usuario lo vea. Es mas seguro pero requiere baja latencia, por eso el budget de 6 segundos.

---

## Distribucion de datos en staging

### Por dia

| Dia | Emails | Allow | Warn | Quarantine | Block |
|-----|--------|-------|------|------------|-------|
| Feb 04 (mar) | 16 | 14 | 2 | 0 | 0 |
| Feb 05 (mie) | 9 | 5 | 3 | 1 | 0 |
| Feb 06 (jue) | 9 | 7 | 2 | 0 | 0 |
| Feb 07 (vie) | 6 | 3 | 1 | 0 | 2 |
| Feb 08 (sab) | 5 | 0 | 1 | 1 | 3 |
| Feb 09 (dom) | 10 | 1 | 1 | 2 | 6 |
| Feb 10 (lun) | 10 | 5 | 3 | 1 | 1 |

### Por tipo

| Categoria | Emails | % |
|-----------|--------|---|
| Legitimos | 42 | 65% |
| Phishing | 13 | 20% |
| BEC | 6 | 9% |
| Malware | 4 | 6% |

### Performance por capa

| Capa | Avg ms | Min ms | Max ms | Avg Score |
|------|--------|--------|--------|-----------|
| Bypass (allowlist) | 351 | 339 | 386 | 0.00 |
| Heuristic | 44 | 41 | 86 | 0.22 |
| ML (DistilBERT) | 310 | 41 | 14383 | 0.42 |
| LLM (GPT-4o-mini) | 4334 | 3019 | 7075 | 0.43 |
