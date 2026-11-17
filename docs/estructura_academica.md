# Estructura académica del proyecto

**Proyecto:** Match Creadores – Extracción de datos de TikTok y análisis de personalidad Big Five
**Institución:** Universidad Central del Ecuador (UCE) · **Grupo:** 5

## 1. Objetivo

Construir un sistema que extraiga datos públicos de un perfil de TikTok, estime los rasgos de personalidad del modelo Big Five (OCEAN) con inteligencia artificial y sugiera a una marca qué tan compatible es el creador con su sector, para apoyar la decisión de colaborar con él.

## 2. Alcance

| Incluye | No incluye |
|---|---|
| Extracción de estadísticas del perfil y de los últimos 10 videos | Diagnóstico psicológico validado |
| Análisis Big Five de las descripciones con IA (API de Groq) | Análisis de audio o imagen de los videos |
| Dashboard web y prototipo de app móvil | Base de datos ni autenticación de usuarios |

## 3. Componentes y responsables de cada etapa

| Etapa | Componente | Archivo o carpeta | Tecnología |
|---|---|---|---|
| 1. Extracción | Scraper de TikTok | `main.py`, `setup_cookies.py` | Python, Playwright |
| 2. Análisis | Estimación Big Five y perfil comercial | `analisis_bigfive.py` | Python, API de Groq |
| 3. Visualización web | Dashboard | `index.html` | HTML, CSS, JavaScript |
| 4. Visualización móvil | App de prototipo | `mobile/` | React Native, Expo, TypeScript |
| 5. Documentación | README y reporte final | `README.md`, `docs/` | Markdown, PDF |

## 4. Flujo de datos

```
Usuario de TikTok -> main.py -> datos_<usuario>.json -> analisis_bigfive.py
        -> (mismo JSON + analisis_bigfive + perfil_comercial) -> index.html / app móvil
```

## 5. Estructura del repositorio

```
match-creadores_grupo5/
├── main.py                 # Extracción (Playwright) y llamada al análisis
├── analisis_bigfive.py     # Análisis Big Five con IA
├── setup_cookies.py        # Preparación de la sesión del navegador
├── index.html              # Dashboard web
├── requirements.txt        # Dependencias de Python
├── README.md               # Guía técnica de uso
├── img/                    # Capturas usadas en el README
├── mobile/                 # App móvil (Expo / React Native)
│   ├── App.tsx             # Navegación entre pantallas
│   └── src/screens/        # Front, Onboarding, Loading, Dashboard,
│                           # Reporte, Sectores compatibles, Propuesta
└── docs/                   # Documentación académica
    ├── estructura_academica.md
    ├── metodologia.md
    ├── prompts.md
    ├── capturas/
    └── reporte_final.pdf
```

## 6. Flujo de la aplicación móvil

Front -> Onboarding (ingreso del usuario) -> Loading -> Dashboard -> Reporte -> Sectores compatibles -> Propuesta enviada.

## 7. Entregables académicos

1. Código fuente en el repositorio de GitHub.
2. `README.md` con instalación, uso y consideraciones éticas.
3. Reporte final en PDF con capturas, metodología y prompts (`docs/reporte_final.pdf`).
