# Revision de Presentacion Guard-IA - Evaluacion Completa

> Ultima actualizacion: 2026-02-07
> Presentacion: "Copia de Guard - IA" (57 slides)
> Contexto: Proyecto final Universidad ORT Uruguay - Strike Security

---

## INDICE

1. [Estructura actual](#estructura-actual)
2. [Evaluacion por principios de presentacion](#evaluacion-por-principios-de-presentacion)
3. [Analisis slide por slide](#analisis-slide-por-slide)
4. [Problemas criticos](#problemas-criticos)
5. [Validacion de congruencia con el codigo](#validacion-de-congruencia-con-el-codigo)
6. [Propuestas de contenido para slides faltantes](#propuestas-de-contenido-para-slides-faltantes)
7. [Checklist de next steps](#checklist-de-next-steps)

---

## Estructura Actual (57 slides)

| # | Seccion | Slides | Contenido |
|---|---------|--------|-----------|
| - | Portada | 1 | GUARD-IA, Presentacion Proyecto Final |
| - | Contenido | 2 | Indice: 8 secciones |
| 01 | Introduccion | 3-6 | Titulo seccion, Equipo, Obj. Academicos, Obj. Proceso |
| 02 | Cliente | 7-10 | Titulo seccion, Strike, Servicios, Clientes |
| 03 | Problema | 11-19 | Titulo, Contexto Whalemate, Problemas, Situacion actual, Validacion riesgo, Usuarios objetivo, Juan Sales (3 slides fraude) |
| 04 | Objetivos | 20-25 | Titulo, Ejemplo con Guard-IA (2 slides), Obj. Negocio (3 slides) |
| 05 | Solucion | 26-29 | Titulo, Solucion, Req. Funcionales, Req. No Funcionales |
| 06 | Arquitectura | 30-35 | Titulo, Tecnologias, Diagrama pipeline, Heuristica, Modelo ML, LLM |
| 07 | AI Agent | 36-40 | Titulo, Hipotesis, Modelos/Objetivo, Prompt (vacia), Demo |
| 08 | Roadmap | 41-56 | Riesgos, Desarrollo, Ciclo vida, Cronograma (3), Hitos, Metricas proceso, Metricas desarrollo, Calidad codigo (vacia), Marco validacion (4), Testing (vacia) |
| - | Cierre | 57 | Gracias |

---

## Evaluacion por Principios de Presentacion

### 1. ESTRUCTURA NARRATIVA (Storytelling)

**Principio:** Una presentacion efectiva cuenta una historia con arco: situacion → conflicto → resolucion → impacto.

| Criterio | Estado | Comentario |
|----------|--------|------------|
| Arco narrativo claro | PARCIAL | Buen arco en secciones 01-04 (problema → urgencia). Se rompe en 05-07 donde se vuelve tecnico sin transiciones |
| Hook inicial | DEBIL | La portada es generica. No hay un dato impactante o pregunta provocadora que enganche desde el segundo 0 |
| Transiciones entre secciones | AUSENTES | Las title slides (3, 7, 11, 20, 26, 30, 36, 41) son solo el nombre de la seccion. No hay frases puente que conecten el "por que" de cada salto |
| Cierre con impacto | DEBIL | La slide 57 es solo "gracias". Falta un cierre que resuma el valor entregado, los logros, o un call-to-action para los evaluadores |

**Next steps:**
- [ ] Agregar un hook en la portada o slide 2 (dato impactante: "El 39.1% de los usuarios en LATAM caen en phishing")
- [ ] Agregar frase puente en cada title slide (ej: "Entendido el problema, veamos a quien afecta..." → Cliente)
- [ ] Reemplazar slide "gracias" con un cierre que tenga: resumen de logros clave + lecciones aprendidas + proximos pasos

### 2. DENSIDAD DE INFORMACION (Signal-to-Noise)

**Principio:** Cada slide debe comunicar UNA idea. Si la audiencia no puede entender la slide en 3 segundos, tiene demasiado texto. Las presentaciones academicas tienden a sobrecargar slides porque quieren "demostrar que saben". El efecto es el opuesto: la audiencia se pierde.

| Criterio | Estado | Comentario |
|----------|--------|------------|
| Una idea por slide | MIXTO | Slides 5-6 (objetivos) son buenas: una idea, 3 puntos. Slides 26-27 (req. funcionales/no funcionales) tienen tablas densas de 8+ filas |
| Texto legible a distancia | PROBLEMA | Las slides de req. funcionales (26-27) tienen tablas con texto pequeno. En una sala de presentacion, las ultimas filas serian ilegibles |
| Balance texto/visual | DESBALANCEADO | Secciones 01-04 tienen buen balance. Secciones 05-08 son casi 100% texto |
| Slides vacias | CRITICO | Slides 38 (Prompt), 50 (Calidad Codigo), 55 (Testing) estan vacias. Es peor tener una slide vacia que no tenerla |

**Next steps:**
- [ ] ELIMINAR slides vacias (38, 50, 55) o completarlas con contenido real antes de presentar
- [ ] Slides 26-27 (requerimientos): considerar mostrar solo los top 3-4 requerimientos en la slide y decir "el detalle completo esta en el documento". La tabla completa se deja para el informe escrito, no para la presentacion oral
- [ ] Agregar mas diagramas/visualizaciones en secciones 05-07 para romper la monotonia de texto

### 3. DISENO VISUAL Y JERARQUIA

**Principio:** El diseno no es decoracion, es comunicacion. La jerarquia visual guia el ojo del espectador hacia lo mas importante primero.

| Criterio | Estado | Comentario |
|----------|--------|------------|
| Consistencia visual | BUENA | Fondo oscuro, tipografia uniforme, uso de azul para destacados. Identidad visual coherente a lo largo de las 57 slides |
| Jerarquia tipografica | BUENA | Titulos grandes, subtitulos diferenciados, cuerpo legible. Se usa bien el peso y tamano |
| Uso del espacio | MIXTO | Muchas slides tienen buen whitespace (5, 6, 14, 15). Otras estan sobrecargadas (26, 27, 47, 51-53) |
| Elementos decorativos | EXCESIVO | El pattern "guard ia- guard ia -" aparece como elemento decorativo repetido en multiples slides. No aporta informacion y ocupa espacio. Considerar reducir su tamano o eliminarlo de slides con mucho contenido |
| Contraste y legibilidad | BUENO | Texto claro sobre fondo oscuro funciona bien. Los highlights en azul tienen buen contraste |

**Next steps:**
- [ ] Reducir el tamano del pattern decorativo "guard ia-" en slides con contenido denso
- [ ] En slides de tablas (26, 27, 47), aumentar el espacio entre filas o usar alternating row colors para mejorar legibilidad

### 4. RITMO Y PACING

**Principio:** Una presentacion de 57 slides a ~1 minuto por slide = ~57 minutos. Si el tiempo asignado es menor, hay que recortar. El ritmo debe alternar entre slides rapidas (impacto visual) y slides lentas (explicacion profunda). Nunca mas de 3 slides densas seguidas.

| Criterio | Estado | Comentario |
|----------|--------|------------|
| Cantidad de slides vs tiempo | POR VALIDAR | 57 slides. Si tienen 30-40 min, es demasiado. Si tienen 60 min, esta ajustado. Verificar tiempo asignado |
| Alternancia rapido/lento | PROBLEMA | Slides 41-55 son 15 slides consecutivas de gestion/metricas/validacion. Es una secuencia muy pesada sin ningun respiro visual |
| Slides de impacto visual | BUENAS | El ejemplo de fraude de Juan (slides 17-22) tiene buen ritmo visual con la narrativa paso a paso |
| Slides de respiracion | FALTAN | No hay slides de transicion que den un respiro entre bloques densos. Las title slides podrian cumplir este rol si tuvieran una frase clave |

**Next steps:**
- [ ] Confirmar el tiempo total de presentacion y ajustar la cantidad de slides
- [ ] Considerar mover el bloque completo de metricas de proceso/desarrollo (slides 48-55) a un anexo, dejando solo 2-3 slides resumen en el cuerpo principal
- [ ] Agregar slides de transicion con una frase clave entre secciones densas

### 5. ENGAGEMENT Y RETENCION

**Principio:** La audiencia recuerda el principio, el final, y los momentos emocionales. Todo lo del medio se olvida a menos que haya algo que lo ancle: una historia, un dato shocking, una demo, una pregunta retorica.

| Criterio | Estado | Comentario |
|----------|--------|------------|
| Momentos memorables | BUENO | El ejemplo de Juan (fraude) es memorable. El dato del 39.1% es impactante. La demo es un ancla fuerte |
| Datos concretos | BUENO | 14.94% not clean, 39.1% error rate LATAM, 7/10 ataques a C-Level/Sales. Buenos numeros |
| Historia humana | BUENO | El personaje de Juan humaniza el problema. Excelente recurso |
| Pregunta retorica | AUSENTE | No hay preguntas retoricas que involucren a la audiencia |
| Demo | PRESENTE | Slide 40 indica "DEMO". Asegurar que la demo funcione en vivo y tener un video backup |

**Next steps:**
- [ ] Agregar al menos 1 pregunta retorica al inicio ("Cuantos de ustedes revisan el remitente de cada email que reciben?")
- [ ] Preparar un video backup de la demo por si falla la conexion/servicio en vivo
- [ ] Considerar abrir con el ejemplo de Juan ANTES de la seccion formal de problema (in medias res) para enganchar

---

## Analisis Slide por Slide

### Portada y Contenido (Slides 1-2)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 1 - Portada | Funcional pero generica. "Presentacion proyecto final" no genera curiosidad | MEJORAR: Agregar subtitulo con value proposition ("Deteccion preventiva de fraude por email con IA") |
| 2 - Contenido | Indice con 8 secciones, correcto. Falta seccion de Validacion/Testing en el indice | CORREGIR: Actualizar si se agregan/quitan secciones |

### 01 - Introduccion (Slides 3-6)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 3 - Title "Introduccion" | Title slide sin frase puente | MEJORAR: Agregar frase puente |
| 4 - Equipo | Roles claros. Nicolas como "Project Manager / DevOps" podria ser mas representativo si hizo mas roles | REVISAR: Validar que los roles reflejen la contribucion real |
| 5 - Objetivos Academicos | Buena. 3 puntos claros, bien estructurados. Buen whitespace | OK |
| 6 - Objetivos del Proceso | Buena. Misma estructura que slide 5. Consistente | OK |

### 02 - Cliente (Slides 7-10)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 7 - Title "Cliente" | Title slide estandar | OK |
| 8 - Strike | Buena introduccion del cliente. "Startup de ciberseguridad con foco en automatizacion e IA" | OK |
| 9 - Servicios | Guard-IA descrita como "Una vista centralizada para todos los correos fraudulentos". Esto es REDUCCIONISTA. Guard-IA no solo visualiza, detecta y previene | CORREGIR: Cambiar a "Deteccion y prevencion de fraude por email con IA" o similar |
| 10 - Clientes | Muestra clientes de Strike. Da credibilidad | OK |

### 03 - Problema (Slides 11-19)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 11 - Title "Problema" | Title slide | OK |
| 12 - Contexto Whalemate | Excelente. Explica el antecedente y por que se necesita Guard-IA | OK |
| 13 - Problemas (phishing, no trust, disorder) | Buenos 3 pilares del problema. Visual y concisa | OK |
| 14 - Situacion Actual | Dato del 14.94% con datos reales de Gmail. Muy fuerte | OK |
| 15 - Validacion del Riesgo | El dato del 39.1% de LATAM es impactante. Bien presentado con comparativa global | OK |
| 16 - Usuarios Objetivo | "7 de cada 10 intentos apuntan a C-Level y Sales". Dato fuerte y accionable | OK |
| 17 - Juan (Sales) - Presentacion | Introduce al personaje. Buen storytelling | OK |
| 18 - Juan - Fraude paso 1 | El atacante envia el email fraudulento | OK |
| 19 - Juan - Fraude paso 2 | "El atacante logra su cometido". Slide quizas redundante con la 18. Evaluar si se pueden fusionar | EVALUAR: Condensar 18+19 en una sola slide |

**La seccion 03 es la mas fuerte de toda la presentacion.** Narrativa clara, datos reales, humanizacion del problema. No tocar mucho.

### 04 - Objetivos (Slides 20-25)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 20 - Title "Objetivos" | Title slide | OK |
| 21 - Ejemplo con Guard-IA paso 1 | Guard-IA intercepta el email de Juan | OK |
| 22 - Ejemplo con Guard-IA paso 2 | Guard-IA bloquea, Juan no recibe el fraude. Cierre del arco narrativo | OK |
| 23 - Objetivos de Negocio (resumen) | Los 3 objetivos en formato corto. Clara y concisa | OK |
| 24 - Objetivos de Negocio (detalle) | Detalle de cada objetivo con metricas concretas (90%, <10%, 100% trazabilidad). Validados con CISO | OK |
| 25 - Slide repetida de "Modelos - Objetivo" | Dice "Definir el modelo base de clasificacion". Esta slide parece estar FUERA DE LUGAR aqui. Es contenido de AI Agent o Arquitectura, no de Objetivos | MOVER o ELIMINAR: Esta slide no pertenece a la seccion Objetivos |

### 05 - Solucion (Slides 26-29)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 26 - Title "Solucion" | Title slide | OK |
| 27 - Solucion | "Un sistema basado en IA orientado a la deteccion preventiva...". Demasiado generica. Falta el COMO: que es un middleware pre-delivery que intercepta via SMTP | MEJORAR: Agregar el diferenciador tecnico clave (pre-delivery, no post-delivery) |
| 28 - Req. Funcionales | Tabla de 8 RF con objetivos y prioridad. Demasiado densa para presentacion oral. La audiencia no va a leer 8 filas | CONDENSAR: Mostrar solo RF1, RF2, RF7 (los criticos) en slide. El resto mencionarlo oralmente o dejarlo en anexo |
| 29 - Req. No Funcionales | Tabla de 6 RNF. Mismo problema de densidad | CONDENSAR: Destacar RNF5 (performance <3s) y RNF6 (escalabilidad 100K emails) como los mas impactantes |

### 06 - Arquitectura (Slides 30-35)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 30 - Title "Arquitectura" | Title slide | OK |
| 31 - Tecnologias | Muestra Cloud Run, Vercel, Clerk, Neon. **FALTA** Google Workspace (pieza fundamental), SMTP Gateway (aiosmtpd), Hugging Face, OpenAI. La slide incluso tiene texto "AGREGAR LO DE HUGGING FACE?" como nota pendiente | CRITICO: Completar con todas las tecnologias. Quitar la nota interna |
| 32 - Diagrama Pipeline | Diagrama del motor de deteccion: Mail → Heuristica → ML → LLM → Veredicto. Buen visual | OK |
| 33 - Heuristica | Explicacion clara de la primera capa. Bien estructurada | OK |
| 34 - Modelo ML | Explicacion del modelo de IA supervisada. Correcta | OK |
| 35 - LLM | Dice "Principalmente detecta: intenciones maliciosas, ingenieria social...". INCORRECTO. El LLM EXPLICA, no detecta. Contradice la arquitectura del sistema | CRITICO: Cambiar "detecta" por "analiza y explica". Reformular la slide completa |

**Faltan slides criticas en esta seccion:**
- Diagrama de arquitectura de ALTO NIVEL (como se conecta todo: email → SMTP → pipeline → Gmail/cuarentena → frontend → backend → DB)
- Ambientes (local / staging / produccion)
- CI/CD pipeline

### 07 - AI Agent (Slides 36-40)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 36 - Title "AI Agent" | Title slide | OK |
| 37 - Hipotesis | H1 (reducir tiempo de analisis) y H2 (mayor precision). Correctas y claras | OK |
| 38 - Modelos/Objetivo | Repetida de slide 25. Objetivo + Estrategia + Criterios de eleccion. Tiene contenido util pero deberia estar consolidada en un solo lugar | CONSOLIDAR: Decidir si va aqui o en Objetivos, no en ambos |
| 39 - Prompt | Solo dice "META PROMPTING ?" con signo de pregunta. Slide completamente vacia/placeholder | CRITICO: Completar con contenido real (estrategia de prompting, system prompt, chain-of-thought) o ELIMINAR |
| 40 - Demo | Referencia a la demo. Critico tenerla funcionando | PREPARAR: Asegurar demo funcional + video backup |

### 08 - Roadmap/Gestion (Slides 41-56)

| Slide | Diagnostico | Accion |
|-------|-------------|--------|
| 41 - Title "Roadmap" | Title slide | OK |
| 42 - Riesgos | Tabla de 4 riesgos con impacto y mitigacion. Buena, pero densa | OK |
| 43 - Desarrollo (Ciclo de vida) | 3 principios del enfoque iterativo. Bien estructurada | OK |
| 44 - Ciclo de vida visual | Diagrama del enfoque iterativo | OK |
| 45 - Cronograma general | Gantt chart. Bueno para dar vision general | OK |
| 46 - Cronograma v0.1 y v0.2 | Detalle de releases. Bueno | OK |
| 47 - Cronograma v0.3 y v1.0 | Detalle de releases | OK |
| 48 - Hitos del proyecto | 4 releases con contenido de cada uno. Buena sintesis | OK |
| 49 - Metricas de proceso | 4 metricas con descripcion. Texto denso | CONDENSAR: Reducir texto, usar graficos o numeros en vez de parrafos |
| 50 - Metricas de desarrollo | 5 metricas de testing. Buena estructura | OK |
| 51 - Calidad de codigo | VACIA. Solo titulo sin contenido | CRITICO: Completar con datos reales (ruff rules, mypy, coverage %) o ELIMINAR |
| 52 - Marco de Validacion | Descripcion de DOD + UAT. Mucho texto | CONDENSAR: Usar diagrama en vez de parrafo |
| 53 - Marco validacion: DOD v0.2 | Detalle de etapas de validacion. Muy detallado para presentacion oral | EVALUAR: Mover a anexo, dejar solo resumen |
| 54 - Marco validacion: UAT tabla | Tabla UAT por release. Bien estructurada | OK |
| 55 - Marco validacion: UAT v1 | Continuacion de UAT. Bien | OK |
| 56 - Testing | VACIA. Solo titulo sin contenido | CRITICO: Completar o ELIMINAR |
| 57 - Gracias | Cierre generico | MEJORAR: Agregar resumen de logros + lecciones aprendidas + proximos pasos |

---

## Problemas Criticos

Estos son los problemas que **deben resolverse antes de presentar**. Estan ordenados por severidad.

### NIVEL 1 - Errores de contenido (corregir si o si)

| # | Slide | Problema | Solucion |
|---|-------|----------|----------|
| C1 | 35 (LLM) | Dice "Principalmente detecta" cuando el LLM solo EXPLICA. Contradice el principio fundamental del proyecto "LLM explains only, never decides" | Cambiar "detecta" por "analiza y explica". Reformular bullet points |
| C2 | 31 (Tecnologias) | Tiene texto interno "AGREGAR LO DE HUGGING FACE?" visible. Es una nota de trabajo, no contenido de presentacion | Quitar la nota. Agregar Hugging Face, Google Workspace, OpenAI, SMTP Gateway (aiosmtpd) |
| C3 | 9 (Servicios) | Guard-IA descrita como "Una vista centralizada para todos los correos fraudulentos". Es incorrecto: Guard-IA DETECTA y PREVIENE, no solo visualiza | Cambiar a "Deteccion y prevencion preventiva de fraude por email con IA" |

### NIVEL 2 - Slides vacias/placeholder (completar o eliminar)

| # | Slide | Problema | Solucion |
|---|-------|----------|----------|
| C4 | 39 (Prompt) | Solo dice "META PROMPTING ?" con signo de pregunta | Completar con la estrategia de prompting real (system prompt, chain-of-thought, few-shot examples) o eliminar |
| C5 | 51 (Calidad codigo) | Titulo sin contenido | Agregar metricas reales: ruff (lint), mypy (types), pytest-cov >= 60%, o eliminar |
| C6 | 56 (Testing) | Titulo sin contenido | Agregar estrategia de testing (unit, integration, e2e) con numeros, o eliminar |
| C7 | 25 y 38 (Modelos) | Slide de "Modelos - Objetivo" aparece duplicada en dos secciones distintas | Consolidar en una sola ubicacion (seccion AI Agent es la mas logica) |

### NIVEL 3 - Contenido faltante critico para la seccion Arquitectura

| # | Que falta | Por que es critico |
|---|-----------|-------------------|
| C8 | Diagrama de arquitectura de alto nivel | Es la slide mas importante de la seccion Arquitectura. Muestra como se conectan TODOS los componentes del sistema. Sin esto, la audiencia no puede entender la vision completa |
| C9 | Slide de ambientes (local/staging/prod) | Demuestra madurez del proyecto y es una pregunta frecuente de evaluadores ("como lo despliegan?") |
| C10 | Slide de CI/CD pipeline | Complementa ambientes y muestra automatizacion del delivery. Diferenciador academico |

---

## Validacion de Congruencia con el Codigo

### Verificado y correcto

| Claim en slides | Realidad del codigo | Estado |
|-----------------|---------------------|--------|
| Pipeline: Heuristica → ML → LLM | `orchestrator.py`: bypass → heuristic → ml → llm → scoring | CORRECTO (hay un bypass check extra) |
| DistilBERT 66M params | `ml_classifier.py` + `train.py`: distilbert-base-uncased 66M | CORRECTO |
| Thresholds: ALLOW <0.3, WARN 0.3-0.6, QUARANTINE >=0.8 | `constants.py`: 0.3, 0.6, 0.8 | CORRECTO |
| Clerk para auth | `security.py`: verify_clerk_token(), RS256 PEM | CORRECTO |
| Neon PostgreSQL | `session.py`: detecta neon.tech hosts | CORRECTO |
| Cloud Run deploy | GitHub Actions: deploy-cloudrun@v2 | CORRECTO |
| Vercel deploy | GitHub Actions + vercel.json | CORRECTO |
| FastAPI + SQLAlchemy async | `pyproject.toml`: FastAPI >=0.115, SQLAlchemy[asyncio] | CORRECTO |
| Vue 3 + TypeScript + Pinia | `package.json`: vue 3.5, ts 5.6, pinia 2.2 | CORRECTO |
| SMTP Gateway funcional | `gateway/server.py` + `handler.py` + `relay.py` | CORRECTO |
| 3 roles: admin, analyst, auditor | `constants.py`: UserRole enum | CORRECTO |
| RF1-RF8 funcionales | Endpoints, services, models implementados | CORRECTO |
| Test coverage >=60% | pyproject.toml: fail_under=60 | CORRECTO |

### Inconsistencias detectadas

| # | Claim | Realidad | Riesgo |
|---|-------|----------|--------|
| I1 | Slide 35: LLM "detecta" intenciones maliciosas | El LLM genera explicaciones (llm_explainer.py). La decision es del orchestrator con weighted average | ALTO - Un evaluador tecnico lo detectaria |
| I2 | RNF5: "<3 segundos por correo" | Budget real: ~5ms (heuristic) + ~18ms (ML) + 2-3s (LLM) = ~3.5s maximo. Sin LLM es <25ms | MEDIO - Depende de latencia de OpenAI. Aclarar que es "en condiciones normales" |
| I3 | "16 tablas" (en documentacion, no en slides) | 14 modelos principales en codigo. Diferencia puede ser tablas de Alembic/system | BAJO - No esta en slides, solo en documentacion |

---

## Propuestas de Contenido para Slides Faltantes

### C8 - Diagrama de Arquitectura de Alto Nivel (NUEVA)

```
ARQUITECTURA GENERAL

                    ┌─────────────────────────────────────────┐
                    │          Google Workspace                │
   Email           │  ┌─────┐    MX     ┌──────────┐         │
   entrante  ───→  │  │ DNS │ ──────→   │  Gmail   │         │
                    │  └─────┘           │ Inbound  │         │
                    │                    │ Gateway   │         │
                    └────────────────────┼──────────┼─────────┘
                                         │          │
                                         ▼          │
                              ┌──────────────────┐  │
                              │  SMTP Gateway    │  │
                              │  (GCP VM:25)     │  │
                              │  aiosmtpd        │  │
                              └────────┬─────────┘  │
                                       │            │
                                       ▼            │
                              ┌──────────────────┐  │
                              │  Detection       │  │
                              │  Pipeline        │  │
                              │  Heur → ML → LLM │  │
                              └───┬────────┬─────┘  │
                                  │        │        │
                          ALLOW   │        │ BLOCK  │
                          /WARN   │        │ /QUAR  │
                                  ▼        ▼        │
                              Forward    Quarantine │
                              to Gmail   + Store    │
                              ◄─────────────────────┘

   ┌──────────┐     ┌──────────────┐     ┌────────┐
   │ Frontend │ ──→ │   Backend    │ ──→ │  Neon  │
   │ (Vercel) │     │ (Cloud Run)  │     │ PgSQL  │
   └──────────┘     └──────────────┘     └────────┘
        │                  │
        └──── Clerk JWT ───┘
```

**Nota:** Este es un esquema logico. En Canva se deberia disenar con iconos/logos y flechas limpias, no con ASCII art.

### C9 - Ambientes (NUEVA)

```
AMBIENTES

┌─────────────────────────────────────────────────┐
│ LOCAL                                            │
│ Docker Compose: PgSQL 16, FastAPI, Vite, MLflow │
│ make dev → levanta todo                          │
│ Puertos: 3000 / 8000 / 5432 / 5000             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ STAGING                                          │
│ Backend: Cloud Run    │ Frontend: Vercel Preview │
│ DB: Neon (branch)     │ Auth: Clerk (test keys)  │
│ CI/CD: GitHub Actions (auto-deploy on push)      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ PRODUCCION                                       │
│ Backend: Cloud Run    │ Frontend: Vercel          │
│ DB: Neon (main)       │ Auth: Clerk (prod keys)   │
│ SMTP: GCP VM e2-micro│ Email: Google Workspace    │
│ Dominio: guardia-sec.com (Namecheap)             │
└─────────────────────────────────────────────────┘
```

### C10 - CI/CD Pipeline (NUEVA)

```
DEPLOYMENT PIPELINE

  Developer
      │
      ▼
  git push → main
      │
      ▼
  GitHub Actions
      │
      ├──→ Tests: pytest (cov >=60%) + ruff + mypy
      │
      ├──→ Backend: Docker build → Artifact Registry → Cloud Run
      │
      └──→ Frontend: npm build → Vercel deploy --prod

  Rollback: Cloud Run revision traffic splitting
  Preview: Vercel genera preview por branch
```

### Slide 35 LLM - Version corregida

Donde dice:
> "Principalmente detecta: Intenciones maliciosas implicitas en el texto del mail. Ingenieria social y manipulacion del lenguaje..."

Deberia decir:
> "Principalmente analiza y explica: Como y donde fueron identificados indicios de fraude. Justifica la accion aplicada (permitir, cuarentena o bloquear). Genera explicaciones claras para el CISO. **No toma decisiones: el score final es un promedio ponderado de Heuristica + ML.**"

### Slide 31 Tecnologias - Version corregida

Agregar las tecnologias faltantes:

```
STACK TECNOLOGICO

Frontend:    Vue 3 + TypeScript + Pinia         → Vercel (CDN global)
Backend:     FastAPI + SQLAlchemy async          → Google Cloud Run
Database:    PostgreSQL 16 (serverless)          → Neon
Auth:        JWT RS256 + roles (invite-only)     → Clerk
Email:       SMTP Gateway + aiosmtpd             → GCP VM (e2-micro)
ML Model:    DistilBERT (66M params)             → Hugging Face
LLM:         GPT (explicaciones)                 → OpenAI
Workspace:   Inbound Gateway + MX routing        → Google Workspace
```

---

## Checklist de Next Steps

### Prioridad CRITICA (hacer antes de la presentacion)

- [ ] **C1** - Slide 35 (LLM): Cambiar "detecta" por "analiza y explica"
- [ ] **C2** - Slide 31 (Tecnologias): Quitar nota "AGREGAR LO DE HUGGING FACE?", completar tecnologias faltantes
- [ ] **C3** - Slide 9 (Servicios Guard-IA): Corregir descripcion reduccionista
- [ ] **C4** - Slide 39 (Prompt): Completar con estrategia real de prompting o ELIMINAR
- [ ] **C5** - Slide 51 (Calidad Codigo): Completar con metricas reales o ELIMINAR
- [ ] **C6** - Slide 56 (Testing): Completar con datos reales o ELIMINAR
- [ ] **C7** - Slides 25 y 38 (Modelos): Consolidar en una sola ubicacion
- [ ] **C8** - CREAR slide de Diagrama de Arquitectura de alto nivel
- [ ] **C9** - CREAR slide de Ambientes (local/staging/prod)

### Prioridad ALTA (mejoran significativamente la presentacion)

- [ ] **C10** - CREAR slide de CI/CD Pipeline
- [ ] Slide 57 (Gracias): Convertir en cierre con impacto (logros + lecciones + proximos pasos)
- [ ] Slides 28-29 (Requerimientos): Condensar tablas, mostrar solo los top 3-4 mas relevantes
- [ ] Slide 27 (Solucion): Agregar el diferenciador "middleware pre-delivery via SMTP"
- [ ] Evaluar condensar slides 18+19 (ejemplo fraude) en una sola
- [ ] Preparar video backup de la demo

### Prioridad MEDIA (principios de buen presenting)

- [ ] Agregar frases puente en title slides de cada seccion
- [ ] Agregar hook en portada o slide 2 (dato impactante)
- [ ] Considerar mover metricas detalladas (slides 48-55) a un anexo, dejando 2-3 slides resumen
- [ ] Reducir tamano del pattern decorativo "guard ia-" en slides con contenido denso
- [ ] Agregar al menos 1 pregunta retorica para engagement
- [ ] Verificar que la cantidad de slides sea compatible con el tiempo asignado

### Prioridad BAJA (nice to have)

- [ ] Slide 4 (Equipo): Revisar si el rol de Nicolas refleja su contribucion real
- [ ] Slide 2 (Indice): Actualizar si se agregan/quitan secciones
- [ ] Considerar reordenar: abrir con el ejemplo de Juan para enganchar (in medias res) y luego ir a la seccion formal

---

## Score General por Seccion

| Seccion | Score | Cambio vs revision anterior | Comentario |
|---------|-------|-----------------------------|------------|
| 01 Introduccion | 8/10 | = | Solida, equipo y objetivos claros |
| 02 Cliente | 8/10 | -1 (por C3) | Strike bien presentado, pero Guard-IA mal descrita en servicios |
| 03 Problema | 9/10 | = | Excelente narrativa con datos reales. La mejor seccion |
| 04 Objetivos | 6/10 | -1 (por C7) | Slide de Modelos fuera de lugar. Ejemplo fraude bien pero largo |
| 05 Solucion | 5/10 | -1 | Demasiado generica, req. funcionales muy densos para oral |
| 06 Arquitectura | 4/10 | -1 (por C2, C8, C9) | Nota interna visible, falta diagrama general, ambientes, CI/CD |
| 07 AI Agent | 3/10 | -1 (por C4) | Slide vacia de Prompt, contenido duplicado, poco desarrollo |
| 08 Roadmap | 7/10 | -1 (por C5, C6) | Cronograma y validacion solidos, pero slides vacias (calidad, testing) |

**Score global: 6.25/10** → Con los fixes criticos y las slides nuevas, podria subir a **8/10**.

---

## Preguntas Frecuentes de Evaluadores (prepararse)

| # | Pregunta probable | Donde esta la respuesta | Preparacion |
|---|-------------------|------------------------|-------------|
| 1 | "Como se integra con el flujo de email real?" | Slide nueva C8 (arquitectura alto nivel) | Tener el diagrama listo y explicar el flujo SMTP |
| 2 | "Que pasa si el sistema falla?" | No hay slide. Mencionarlo oralmente | Fail-open: si Guard-IA cae, el email se entrega igual. Nunca bloquea email legitimo por error del sistema |
| 3 | "Como miden la efectividad del modelo?" | Slide 50 (metricas desarrollo) parcialmente | Preparar numeros: precision, recall, F1, ROC-AUC del modelo entrenado |
| 4 | "Por que DistilBERT y no otro?" | Slide 38 (modelos) parcialmente | 66M params (vs BERT 110M), latencia <20ms, fine-tunable, suficiente para clasificacion binaria |
| 5 | "Como manejan falsos positivos?" | Slide 24 (obj. negocio) | RF5: liberacion en <=2 clicks. El analista revisa en el dashboard y libera |
| 6 | "Que diferencia hay entre ambientes?" | Slide nueva C9 | Tener la slide lista con local/staging/prod |
| 7 | "Como despliegan?" | Slide nueva C10 | GitHub Actions → Cloud Run / Vercel |
| 8 | "El LLM puede ser manipulado?" | No hay slide. Mencionarlo oralmente | El LLM solo explica. Nunca decide. El score es weighted average de heuristica + ML. Aunque el LLM falle, el sistema sigue funcionando |
| 9 | "Que datasets usaron?" | Parcial en slide 38 | Datasets publicos de phishing + casos reales de Strike. Preparar numeros (cuantos samples, split train/val/test) |
| 10 | "Como escala a 100K emails/dia?" | RNF6 en slide 29, sin detalle tecnico | Cloud Run auto-scaling, pipeline async, PostgreSQL Neon serverless |
