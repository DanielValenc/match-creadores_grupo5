# Metodología

## 1. Enfoque

Proyecto de desarrollo de software aplicado, con una arquitectura en tres etapas (extracción, análisis y visualización) y entregas incrementales, que se pueden seguir en el historial de commits del repositorio (del 18 de octubre al 15 de noviembre de 2026).

## 2. Etapas

### 2.1 Extracción de datos (`main.py`)

1. Se abre Chromium con **Playwright** y una sesión persistente (`perfil_tiktok/`) para reducir los Captchas.
2. Se entra a `https://www.tiktok.com/@usuario`.
3. Se extraen siguiendo, seguidores, me gusta y la foto de perfil.
4. Se hace scroll simulado para que TikTok cargue los videos.
5. Se capturan el enlace, la miniatura y la descripción de cada video, sin duplicados, y se conservan los primeros 10.
6. Se guarda todo en `datos_<usuario>.json` (UTF-8).

Si TikTok muestra un Captcha (captura 3), el programa espera hasta 60 segundos a que se resuelva manualmente.

### 2.2 Análisis con IA (`analisis_bigfive.py`)

1. Se leen las descripciones de los videos y se descartan las vacías o con el texto "Sin descripción disponible".
2. Se unen en un solo texto, limitado a 6000 caracteres.
3. Se envía a la API de Groq un prompt (ver `prompts.md`) con temperatura 0.3 para obtener respuestas más estables.
4. Se pide que la respuesta sea únicamente un JSON con 9 claves: cinco rasgos (0 a 100), resumen, tono de comunicación, intereses y afinidad con categorías de marca.
5. Se **valida** la respuesta: se ignoran los bloques `<think>` y el texto extra, se comprueba que estén los 5 rasgos con valores entre 0 y 100 y se descartan las categorías de marca que no pertenezcan a la lista permitida.
6. Se **normalizan** los cinco puntajes para que sumen exactamente 100 (método del mayor resto), de modo que se puedan comparar entre sí.
7. Se guarda el resultado en el mismo JSON bajo `analisis_bigfive` y `perfil_comercial`.

### 2.3 Visualización

- **Dashboard web (`index.html`):** lee el JSON con `fetch()` y muestra perfil, estadísticas, barras de cada rasgo, resumen y cuadrícula de videos (capturas 1 y 2).
- **App móvil (`mobile/`):** prototipo en React Native con el flujo Front, Onboarding, Loading, Dashboard, Reporte, Sectores compatibles y Propuesta.

## 3. Modelo de personalidad: Big Five (OCEAN)

| Rasgo | Descripción |
|---|---|
| Apertura | Curiosidad y creatividad |
| Responsabilidad | Organización y disciplina |
| Extraversión | Energía social |
| Amabilidad | Empatía y cooperación |
| Neuroticismo | Sensibilidad emocional |

La IA entrega cada rasgo de 0 a 100 y luego el sistema los normaliza para que los cinco sumen 100.

## 4. Herramientas

Python 3.9+, Playwright, requests, python-dotenv, API de Groq, HTML/CSS/JavaScript, React Native con Expo, Git y GitHub.

## 5. Validación

Se probó el flujo completo con un perfil de ejemplo (`@danielvalencia365`): se extrajeron 10 videos, se generó el análisis y el dashboard mostró correctamente los resultados (capturas 1 y 2).

## 6. Limitaciones y ética

- No es un test psicológico validado: la IA estima rasgos a partir de pocas descripciones y hashtags, y los porcentajes son orientativos.
- La muestra es pequeña (10 videos).
- Se usan únicamente cuentas públicas, con fines educativos y, cuando es posible, con consentimiento de la persona.
- El scraping puede ir contra los términos de uso de TikTok y su estructura cambia con frecuencia.
- Las descripciones se envían a un tercero (Groq) para procesarlas.
- La clave de la API se guarda en `.env`, que no se sube a Git.
