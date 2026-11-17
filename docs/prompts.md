# Prompts utilizados

## 1. Prompts dentro del sistema (código)

Estos prompts están en `analisis_bigfive.py` y se envían a la API de Groq en cada análisis.

### 1.1 Mensaje de sistema

```
You output only valid JSON without markdown formatting.
```

Su función es evitar que el modelo agregue texto o formato markdown, para poder leer la respuesta directamente como JSON.

### 1.2 Mensaje de usuario

```
Actúa como un analista de marketing con conocimientos de psicología computacional.
Analiza el siguiente texto extraído de los últimos videos de una cuenta de TikTok (descripciones y hashtags).
Tu objetivo es estimar su personalidad con el modelo Big Five (O.C.E.A.N.) y determinar con qué tipo de
productos o servicios podría estar alineada, para ayudar a una marca a decidir si colabora con esta persona.

Devuelve ÚNICAMENTE un objeto JSON válido con exactamente 9 claves:
1. "Apertura" (número entero 0-100)
2. "Responsabilidad" (número entero 0-100)
3. "Extraversion" (número entero 0-100)
4. "Amabilidad" (número entero 0-100)
5. "Neuroticismo" (número entero 0-100)
6. "resumen" (un párrafo de máximo 3 líneas describiendo la personalidad general y el estilo de esta persona).
7. "tono_comunicacion" (máximo 8 palabras, por ejemplo: cercano, humorístico y espontáneo).
8. "intereses" (lista de 3 a 5 temas principales que aparecen en su contenido).
9. "afinidad_marcas" (lista de exactamente 3 objetos, ordenados de mayor a menor afinidad; cada objeto tiene
   la clave "categoria" y la clave "motivo", una frase corta que explique la afinidad basándose en el texto).
   El valor de "categoria" debe ser exactamente una de estas opciones: {lista de categorías}.

Texto a analizar: {descripciones de los videos}
```

### 1.3 Decisiones de diseño del prompt

| Decisión | Motivo |
|---|---|
| Rol de analista de marketing con psicología computacional | Orienta la respuesta al uso comercial (decidir si una marca colabora con el creador). |
| Salida limitada a un JSON con 9 claves exactas | Permite validar la respuesta automáticamente. |
| Rasgos como enteros de 0 a 100 | Se pueden dibujar como barras en el dashboard (después se normalizan para que sumen 100). |
| Categorías de marca de una lista cerrada | Evita respuestas inventadas y facilita mostrar los sectores compatibles. |
| Temperatura 0.3 | Respuestas más consistentes entre ejecuciones. |
| Texto limitado a 6000 caracteres | Controla el tamaño de la petición. |

### 1.4 Resultado de ejemplo

Para `@danielvalencia365` (valores de la captura 1): Apertura 75, Responsabilidad 60, Extraversión 85, Amabilidad 80 y Neuroticismo 20, con un perfil descrito como extrovertido y sociable, con interés en cultura pop, viajes y experiencias compartidas.

## 2. Prompts usados durante el desarrollo con asistentes de IA

<!-- COMPLETAR: pega aquí los prompts reales que usaron tú o tu grupo con ChatGPT, Claude, Copilot, etc. -->

| N.º | Herramienta | Prompt | Para qué se usó | Resultado |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
