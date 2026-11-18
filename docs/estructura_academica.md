# Estructura académica del proyecto

**Proyecto:** TrueMatch AI · Inteligencia de creadores para marcas
**Institución:** Universidad Central del Ecuador (UCE) · Dispositivos Móviles · **Grupo 5**
**Integrantes:** Nicolás Caiza · Daniel Valencia · Jair Folleco · Karen García

## 1. Objetivo

Construir un sistema que analice el perfil público de un creador de TikTok y entregue a una marca tres respuestas, aplicando **Domain-Driven Design (DDD)**:

1. **¿Quién es el creador?** Perfil Big Five con citas literales que respaldan cada rasgo, tono de comunicación e intereses.
2. **¿Su audiencia es real?** Auditoría estadística de sus métricas con la Ley de Benford.
3. **¿Con qué sectores encaja?** Categorías de marca afines, con el motivo de cada una.

## 2. Alcance

| Incluye | No incluye |
|---|---|
| Extracción del perfil público y de hasta 30 videos, con sus cinco métricas | Diagnóstico psicológico validado |
| Big Five con citas literales verificadas (API de Groq) | Análisis de audio o imagen de los videos |
| Auditoría de audiencia con la Ley de Benford | Base de datos ni autenticación de usuarios (se guarda en JSON) |
| Backend en capas DDD, línea de comandos y dashboard web | Brand Matching completo y envío de propuestas (en progreso) |
| App móvil en Expo con las 7 pantallas del prototipo | App móvil conectada al backend (en progreso) |

## 3. Diseño con DDD

| Contexto acotado | Tipo de subdominio | Responsabilidad | Estado |
|---|---|---|---|
| Creator Profiling | De soporte | Obtener el perfil y los videos; estimar personalidad, tono e intereses con evidencia | Implementado |
| Audience Audit | De soporte | Determinar qué tan orgánica es la audiencia a partir de sus métricas | Implementado |
| Brand Matching | Principal (core) | Afinidad por sector, puntaje de match y propuestas | En progreso |

Capas y regla de dependencia: `interfaces → application → domain ← infrastructure`. El dominio solo usa la biblioteca estándar de Python.

## 4. Componentes de cada etapa

| Etapa | Componente | Ubicación | Tecnología |
|---|---|---|---|
| 1. Extracción | `TikTokCreatorSource` (capa anticorrupción) y motor SCRAPINGTIKTOK | `backend/truematch/infrastructure/tiktok/` | Python, Playwright |
| 2. Auditoría | `AuditAudience`, `AudienceAudit`, análisis de Benford | `domain/audience_audit/`, `application/use_cases/` | Python (biblioteca estándar) |
| 3. Personalidad | `GroqPersonalityAnalyzer`, verificación de citas | `infrastructure/ai/`, `domain/creator_profiling/` | API de Groq |
| 4. Persistencia | `LegacyJsonCreatorRepository` | `infrastructure/persistence/` | Archivos `datos_<usuario>.json` |
| 5. Interfaces | Línea de comandos y dashboard web | `interfaces/cli/`, `interfaces/web/` | Python, Flask |
| 6. App móvil | Maqueta navegable de 7 pantallas | `mobile/` | React Native, Expo, TypeScript |
| 7. Documentación | README, reporte y evidencias | `README.md`, `docs/` | Markdown, Word/PDF |

## 5. Flujo de datos

```
Marca -> usuario de TikTok -> AnalyzeCreator
   -> TikTokCreatorSource  (Creator con hasta 30 videos)
   -> AuditAudience        (AudienceAudit: puntaje o motivo de su ausencia)
   -> GroqPersonalityAnalyzer (PersonalityAnalysis con citas verificadas)
   -> CreatorRepository    (datos_<usuario>.json)
   -> dashboard web / CLI / app móvil
```

Si falla la IA, se conservan la extracción y la auditoría. Si falla la extracción, no se guarda nada.

## 6. Estructura del repositorio

```
match-creadores_grupo5/
├── README.md
├── requirements.txt
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── tests/                              Pruebas trasplantadas de media-scraper
│   └── truematch/
│       ├── domain/                         Sin dependencias externas
│       │   ├── creator_profiling/
│       │   │   ├── username.py             Username
│       │   │   ├── counts.py               Regla "entero o desconocido"
│       │   │   ├── video.py                Video, VideoStats
│       │   │   ├── public_profile.py       PublicProfile
│       │   │   ├── creator.py              Creator (raíz del agregado)
│       │   │   ├── big_five.py             Trait, TraitScore, TraitStatus, BigFiveProfile
│       │   │   ├── trait_evidence.py       TraitEvidence, verificación de citas
│       │   │   └── personality_analysis.py PersonalityAnalysis
│       │   ├── audience_audit/
│       │   │   ├── benford.py              Análisis de Benford
│       │   │   ├── organic_score.py        OrganicScore y sus mínimos
│       │   │   └── audience_audit.py       AudienceAudit
│       │   └── brand_matching/             En progreso
│       ├── application/
│       │   ├── ports/
│       │   │   ├── creator_source.py
│       │   │   ├── personality_analyzer.py
│       │   │   └── creator_repository.py
│       │   └── use_cases/
│       │       ├── analyze_creator.py
│       │       ├── audit_audience.py
│       │       └── analyze_personality.py
│       ├── infrastructure/
│       │   ├── config.py                   Configuración: clave, modelo, carpetas
│       │   ├── tiktok/
│       │   │   ├── session.py              Sesión persistente de Chromium con bloqueo
│       │   │   ├── runtime.py              Controles de acceso e identidad
│       │   │   ├── adapter.py              Salida del motor → contrato propio
│       │   │   ├── tiktok_creator_source.py  Capa anticorrupción → Creator
│       │   │   └── vendor/scrapingtiktok/  Motor de terceros (MIT), con su licencia
│       │   ├── ai/
│       │   │   ├── groq_client.py          Cliente HTTP de Groq
│       │   │   ├── prompts.py              Prompt con referencias p1…pN
│       │   │   ├── json_extractor.py
│       │   │   └── groq_personality_analyzer.py  Capa anticorrupción → BigFiveProfile
│       │   └── persistence/
│       │       └── legacy_json_repository.py     datos_<usuario>.json
│       └── interfaces/
│           ├── cli/
│           │   ├── main.py                 Subcomandos
│           │   └── formatting.py           Salida de consola
│           └── web/
│               ├── app.py                  Servidor Flask
│               └── templates/index.html    Dashboard
└── mobile/                                 App TrueMatch AI (Expo)
    ├── App.tsx
    ├── index.ts
    ├── app.json · package.json · tsconfig.json
    ├── assets/
    └── src/
        ├── screens/                        Las 7 pantallas del prototipo
        ├── components/
        └── theme.ts
```

*Nota: En el directorio raíz no se encuentran scripts sueltos de ejecución; todo el backend está modularizado y se gestiona internamente desde la estructura establecida.*

## 7. Flujo de la aplicación móvil

Front → Onboarding (ingreso del usuario de TikTok) → Loading → Dashboard → Reporte → Sectores → Propuesta.

## 8. Responsables

| Integrante | Aporte principal |
|---|---|
| Nicolás Caiza | Arranque en Expo Go, diseño DDD, backend en capas: motor de extracción, auditoría Benford, Big Five con evidencia, CLI |
| Daniel Valencia | Proyecto original (scraper y enriquecimiento inicial); revisión y aprobación de pull requests |
| Jair Folleco | Dashboard web en Flask y su diseño |
| Karen García | Estructura académica y reporte de evidencia |

## 9. Entregables académicos

1. Código fuente en el repositorio de GitHub (ramas `main`, `dev` y `feature/<nombre>`, con pull requests).
2. `README.md` con integrantes, problema, modelo de negocio, Figma, DDD, instalación y uso.
3. Reporte final con capturas, metodología, estructura académica y prompts (`docs/reporte_final.pdf`).