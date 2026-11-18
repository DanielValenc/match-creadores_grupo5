# Prompts utilizados

## 1. Prompts dentro del sistema (código)

El prompt vive en `backend/truematch/infrastructure/ai/prompts.py` y se envía a la API de Groq en cada análisis (adaptador `GroqPersonalityAnalyzer`).

### 1.1 Mensaje de sistema

<!-- COMPLETAR: pegar el texto exacto del mensaje de sistema desde prompts.py -->

### 1.2 Mensaje de usuario

<!-- COMPLETAR: pegar el texto exacto del prompt de usuario desde prompts.py, con {descripciones con referencias p1…pN} y {catálogo de categorías} como marcadores -->

### 1.3 Decisiones de diseño del prompt

| Decisión | Motivo |
|---|---|
| Cada video se envía con una referencia corta `p1…pN` | El modelo no inventa identificadores de video |
| Por rasgo se pide un puntaje de 0 a 100 y citas literales breves | Cada puntaje queda respaldado por texto verificable |
| Los cinco rasgos son independientes (no se normalizan a 100) | Así funciona el modelo Big Five |
| Categorías de marca de un catálogo cerrado | Evita categorías inventadas; el dominio descarta las que no pertenecen al catálogo |
| Solo se envían las descripciones de los videos | No se envían comentarios de terceros ni métricas |

### 1.4 Control aplicado a la respuesta

| Control | Qué hace |
|---|---|
| Verificación de citas | Cada cita se busca literalmente en la descripción del video citado; si no aparece, se descarta |
| Regla de los 2 videos | Un rasgo solo conserva su puntaje con citas válidas de al menos 2 videos distintos |
| Resumen rotulado | El resumen es texto libre del modelo y se muestra como "no verificado" |

### 1.5 Resultado de ejemplo

Para `@danielvalencia365` (ver `docs/capturas/`): Apertura 85, Extraversión 75 y Amabilidad 80, cada uno respaldado por citas de 3 videos de los 20 analizados. Responsabilidad y Neuroticismo: "Evidencia insuficiente". Tono: "Cercano, entusiasta y orientado a la comunidad". Intereses: lectura y BookTok, viajes y parques temáticos, cine y series, parejas y relaciones, música y conciertos. Afinidad de marca: Educación y cursos, Viajes y turismo, Entretenimiento y gaming.

## 2. Prompts usados durante el desarrollo con asistentes de IA

Herramientas declaradas en el README (sección 17): **Claude (Anthropic)** y **Claude Code**. Cada cambio fue revisado y confirmado manualmente por el equipo.

<!-- COMPLETAR: pegar los prompts reales (o su resumen fiel) y el resultado. Cada integrante agrega los suyos. -->

| N.º | Herramienta | Prompt | Para qué se usó | Resultado |
|---|---|---|---|---|
| 1 | Claude | | Análisis del proyecto frente a la consigna | |
| 2 | Claude | | Diseño estratégico y táctico de DDD | |
| 3 | Claude Code | | Migración del backend por pasos, un commit por paso | |
| 4 | Claude | | Redacción de la documentación (README y reporte) | |
