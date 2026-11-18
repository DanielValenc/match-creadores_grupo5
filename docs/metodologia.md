# Metodología

## 1. Enfoque

Proyecto de desarrollo de software aplicado, organizado con **Domain-Driven Design (DDD)**: el backend se estructura alrededor del negocio y no de la tecnología. Las decisiones del diseño estratégico (dominio, contextos acotados, lenguaje ubicuo) se documentan primero en la sección 6 del README y mandan sobre el código.

El trabajo es incremental y se puede seguir en el historial de commits: un commit por cambio verificado, con Conventional Commits.

## 2. Diseño estratégico

- **Dominio:** ayudar a las marcas a encontrar creadores de TikTok que encajen con ellas, según quién es el creador, qué tan real es su audiencia y con qué sectores es compatible.
- **Contextos acotados:** Creator Profiling, Audience Audit y Brand Matching (este último en progreso).
- **Lenguaje ubicuo:** `Creator`, `Username`, `PublicProfile`, `Video`, `VideoStats`, `BigFiveProfile`, `TraitScore`, `TraitEvidence`, `AudienceAudit`, `OrganicScore`, `Sector`, `MatchScore`, `Proposal`.
- **Capas anticorrupción:** un adaptador traduce TikTok a un `Creator` y otro traduce la respuesta de Groq a un `BigFiveProfile`. Si cambia el sistema externo, solo cambia su adaptador.

## 3. Diseño táctico

Regla de dependencia: `interfaces → application → domain ← infrastructure`. La regla se verifica analizando los imports de cada archivo y no tiene violaciones.

Reglas del dominio más importantes:

1. Una métrica es un entero mayor o igual a cero, o desconocida; lo desconocido nunca se convierte en cero.
2. Cada `TraitScore` es un entero de 0 a 100 y los cinco rasgos son independientes (no se normalizan a 100).
3. Una cita solo es válida si aparece literalmente en la descripción del video que cita.
4. Un rasgo solo conserva su puntaje si tiene citas válidas de al menos 2 videos distintos.
5. El `OrganicScore` solo se calcula con al menos 110 valores válidos que abarquen 2 órdenes de magnitud.

## 4. Etapas del sistema

### 4.1 Extracción de datos (contexto Creator Profiling)

1. Chromium, controlado por Playwright, se abre con una sesión persistente iniciada una vez con el comando `session`.
2. El motor SCRAPINGTIKTOK (licencia MIT) recorre el perfil y abre cada video, hasta un máximo de 30.
3. Se leen siguiendo, seguidores, me gusta y, por video, identificador, enlace, descripción, fecha, vistas, me gusta, comentarios, compartidos y guardados, como enteros exactos.
4. La capa anticorrupción verifica que el perfil y cada video sean los solicitados. Un video inaccesible se omite y no se rellena con datos inventados.
5. Si TikTok pide verificación, la extracción se detiene; no se intenta resolver ni evadir.
6. No se recogen listas de seguidores ni comentarios de terceros.

### 4.2 Big Five con evidencia verificada

1. Cada video se envía a Groq con una referencia corta `p1…pN`, para que el modelo no invente identificadores.
2. Por cada rasgo, el modelo propone un puntaje de 0 a 100 y citas literales breves.
3. El dominio compara cada cita con la descripción original (solo se toleran diferencias de espacios y de composición Unicode) y descarta las que no aparecen.
4. Si un rasgo tiene citas válidas de al menos 2 videos distintos, se publica con estado `scored`. Si no, queda sin puntaje (`insufficient_evidence`).
5. Se informa la cobertura (en cuántos videos hay evidencia), pero nunca se usa como puntaje.
6. El resumen es texto libre del modelo y se rotula como **no verificado**.

### 4.3 Auditoría de audiencia con la Ley de Benford (contexto Audience Audit)

1. Se juntan las cinco métricas de todos los videos (hasta 150 valores).
2. Se excluyen ausentes y ceros, y se informa cuántos de cada tipo.
3. Se calcula la distribución observada del primer dígito significativo y se compara con la esperada, `P(d) = log10(1 + 1/d)`, usando la desviación absoluta media (MAD).
4. Hay puntaje orgánico solo con al menos 110 valores válidos y 2 órdenes de magnitud; si no, el resultado es "Sin puntaje" con el motivo exacto.
5. La conversión de la MAD al puntaje de 0 a 100 está en recalibración, por lo que el puntaje es provisional.
6. Una desviación respecto de Benford no demuestra bots, fraude ni compra de seguidores.

### 4.4 Interfaces

- **Línea de comandos:** `session`, `analyze`, `bigfive`, `audit`, `web`.
- **Dashboard web (Flask):** perfil, Big Five con radar y citas enlazadas a cada video, perfil comercial, auditoría con gráfico de dígitos y los videos extraídos.
- **App móvil (Expo):** maqueta navegable de las 7 pantallas del prototipo de Figma; la conexión con el backend está en progreso.

## 5. Flujo de trabajo del equipo

| Rama | Uso |
|---|---|
| `main` | Versión de entrega. Solo recibe cambios desde `dev` |
| `dev` | Integración. Todo entra por pull request con una aprobación |
| `feature/<nombre>` | Trabajo de cada integrante |

## 6. Herramientas

Python 3.10+, Playwright, Flask, `requests`, `filelock`, API de Groq (modelo Qwen), React Native con Expo (SDK 58) y TypeScript, Figma, Git y GitHub. Durante el desarrollo se usaron asistentes de IA: Claude y Claude Code (ver `prompts.md`).

## 7. Validación

- **Pruebas automáticas:** `test_benford.py`, `test_reference_engine.py` y `test_browser.py`, ejecutadas con `python -m unittest`. Las pruebas provienen del proyecto media-scraper y se trajeron junto con el código que verifican.
- **Prueba con un perfil real:** se analizó `@danielvalencia365` con 20 videos extraídos. El Big Five publicó Apertura 85, Extraversión 75 y Amabilidad 80, cada uno con citas de 3 videos; Responsabilidad y Neuroticismo quedaron como "Evidencia insuficiente". La auditoría de Benford quedó "Sin puntaje": 86 valores válidos de 110 necesarios, con 14 métricas en cero excluidas (capturas en `docs/capturas/`).

## 8. Limitaciones y ética

- El análisis de personalidad usa solo texto (descripciones de los videos) y no es un test psicométrico.
- La muestra es de hasta 30 videos y la extracción puede ser parcial.
- El puntaje orgánico es provisional y las cinco métricas de un mismo video no son independientes.
- Se usan solo cuentas públicas, con fines académicos. La extracción automatizada puede ir contra los términos de uso de TikTok.
- Las descripciones de los videos se envían a Groq para su análisis.
- Los resultados son un apoyo; no deben tomarse decisiones sobre una persona solo con estas estimaciones.
- La clave de Groq se guarda en `.env`, que no se sube a Git.
