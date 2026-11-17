# Plan de backend: trasplante desde media-scraper en capas DDD

Plan para reestructurar el backend Python según la [sección 6 del README](../README.md#6-metodología-domain-driven-design)
y completar lo que le falta tomando código de **media-scraper** (rama `feature/setup-inicial`, commit `a3ef81d`).

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Videos por análisis | **30** (`MAX_VIDEOS = 30`) |
| Benford | Se **juntan las 5 métricas** (vistas, me gusta, comentarios, compartidos, guardados) de todos los videos: hasta 150 valores |
| Big Five | `TraitScore` **puede ser nulo** cuando no hay evidencia suficiente |
| Bloqueo de la sesión de Chromium | **`filelock`** (funciona en Linux, macOS y Windows) |
| Pruebas | **Solo se traen las que ya existen en media-scraper**; no se escriben pruebas nuevas |
| Persistencia | JSON en disco (sin MongoDB) |
| IA | Groq (sin OpenAI, embeddings ni PCA) |

## Hallazgos que condicionan el plan

1. **El scraper que funciona en media-scraper no es `scraper.py`.** La API y `manage.py` usan
   `reference_engine.scrape_profile`, que ejecuta el motor externo **SCRAPINGTIKTOK** (Jccasav14, licencia MIT,
   commit `7deb6d0`) incluido en `backend/vendor/scrapingtiktok/`. Además, `scraper.py` convierte los números
   exactos en textos como "1.2K" (`format_metric`), lo que arruina Benford. No se trasplanta.
2. **El motor entra a cada video.** No intercepta `/api/post/item_list/`: recorre la cuadrícula del perfil, ordena
   por ID (más alto = más reciente) y abre cada video para leer `webapp.video-detail` del JSON
   `__UNIVERSAL_DATA_FOR_REHYDRATION__`. Con 30 videos, un análisis tarda varios minutos.
3. **El Benford de media-scraper no da puntaje a propósito** (`docs/benford.md`: nunca clasifica una cuenta como
   que «cumple» o «no cumple»). Este proyecto necesita `OrganicScore`, así que se agrega una política propia encima
   (ver «Conciliación»).
4. **`session.py` usa `fcntl`**, que solo existe en Linux y macOS. Se reemplaza por `filelock`.
5. **El motor recorre las listas de seguidores y seguidos y los comentarios** aunque se le pase `0`. No se
   necesitan (tiempo y datos de terceros). Hace falta un parche pequeño, registrado en `INTEGRATION.patch` y
   `PROVENANCE.json`.

## 1. Qué cubre cada carencia

| Carencia | Origen en media-scraper |
|---|---|
| Métricas por video | Motor `vendor/scrapingtiktok/tiktok_scraper.py` (`TikTokScraper.scrape`, `_extract_video_urls`, `_extract_single_video_details`): lee `stats.playCount/diggCount/commentCount/shareCount/collectCount`, `createTime`, `desc`, `challenges`, `duration` |
| | `reference_adapter.py` (`adapt_profile`, `metric`, `timestamp`): pasa a enteros exactos y verifica la autoría |
| | `reference_runtime.py` (`checked_int`, `metric_dict`, `publication_url`, `verified_profile`, `verified_publication`, `validate_access`, `persistent_playwright`, `setup_persistent_context`, `GuardedPage`) |
| | `reference_engine.py` (`extract_profile`, `scrape_profile`): punto de entrada con `asyncio.run` |
| Sesión persistente | `session.py` (`profile_lock`, `persistent_context`, `configure_session`, `SessionBusyError`, `private_directory`). Reemplaza `perfil_tiktok/` y `setup_cookies.py` (que escribe un `state.json` que nadie lee) |
| Normalización de contadores | `normalizer._counter_value` ("18.6K" → 18600; inválido → `None`). Solo para leer los `datos_*.json` antiguos. No se usa `normalize_number` (convierte lo ausente en 0) ni `normalize_profile` (forma de Mongo) |
| Benford | `benford.py` completo (`benford_probabilities`, `numeric_value`, `first_significant_digit`, `analyze_values`, `DISCLAIMER`). De `benford_repository.py` solo la idea de quitar duplicados por ID; de `benford_routes.py` solo el esquema de respuesta |
| Extras | `demo.py` (capturas para modo demo), `manage.py` (comandos `session` y `capture`), `semantic_analysis.canonical_text` y la comprobación de citas de `validate_finding`, tabla de errores de `backend/main.py` |

## 2. Dependencias

| Pieza | Dependencias | ¿Se trasplanta? |
|---|---|---|
| `benford.py` | stdlib | Sí, tal cual |
| `normalizer._counter_value` | stdlib | Solo esa función |
| `session.py` | `playwright` sync, `fcntl` | Sí, con `filelock` en lugar de `fcntl` |
| Motor + `reference_runtime` + `reference_adapter` + `reference_engine` | `playwright.async_api`, stdlib | Sí, con `LICENSE` y `PROVENANCE.json` |
| `demo.py`, `manage.py` | stdlib | Sí, adaptados |
| `canonical_text` + comprobación de citas | stdlib (`unicodedata`) | Sí, sin Pydantic |
| `benford_repository.py`, `benford_routes.py` | `pymongo`, `fastapi` | Solo lógica y esquema |
| `ocean_analysis.py`, `semantic_*`, `embeddings*`, `semantic_projection`, `structured_analysis`, `database`, `repository`, `stored_profiles`, `frontend/` | OpenAI, Mongo | No |
| `scraper.py` | `playwright` sync | No |

`requirements.txt` (paso 2):

- **Se añaden:** `fastapi==0.146.0`, `uvicorn==0.54.0`, `pydantic==2.14.1` (con sus dependencias) y `filelock`.
- **Se mantienen:** `playwright==1.64.0` (sin duplicado), `requests` y `python-dotenv`.
- **Se excluyen:** `pymongo`, `dnspython`, `openai` y `opentelemetry-api`.
- **Pruebas:** las de media-scraper usan `unittest`, así que se ejecutan con `python -m unittest` sin añadir dependencias.

## 3. Estructura y destino de cada pieza

```
backend/
├── pyproject.toml
├── truematch/
│   ├── domain/
│   │   ├── creator_profiling/   Username, Video, VideoStats, PublicProfile, Creator, BigFiveProfile, TraitScore, TraitEvidence
│   │   ├── audience_audit/      BenfordAnalyzer, AudienceAudit, OrganicScore
│   │   └── brand_matching/      Sector, SectorAffinity, MatchScore, MatchCalculator, Brand, Proposal
│   ├── application/
│   │   ├── ports/               CreatorSource, CreatorRepository, PersonalityAnalyzer, ProposalRepository
│   │   └── use_cases/           AnalyzeCreator, AuditAudience, GetCompatibleSectors, GetMatchReport, SendProposal
│   ├── infrastructure/
│   │   ├── tiktok/              motor SCRAPINGTIKTOK, runtime, session, TikTokCreatorSource
│   │   ├── ai/                  cliente Groq, prompts, analizador de personalidad
│   │   └── persistence/         repositorio JSON, formato heredado, capturas demo
│   └── interfaces/
│       ├── api/                 FastAPI
│       └── cli/                 comandos session, capture, analyze, audit
└── tests/
```

| Origen (media-scraper) | Destino (`backend/truematch/`) |
|---|---|
| `benford.py` | `domain/audience_audit/benford.py` |
| (nuevo) política de puntaje | `domain/audience_audit/organic_score.py`, `audience_audit.py` |
| `USERNAME` / `validate_username` | `domain/creator_profiling/username.py` (unificado con el de Jair, que usa 2–24 caracteres) |
| `canonical_text` + comprobación de citas | `domain/creator_profiling/trait_evidence.py` |
| Lógica de `benford_repository` | `application/use_cases/audit_audience.py` |
| `vendor/scrapingtiktok/*` | `infrastructure/tiktok/vendor/scrapingtiktok/` |
| `reference_runtime.py` | `infrastructure/tiktok/runtime.py` |
| `session.py` | `infrastructure/tiktok/session.py` (carpeta `.truematch/chromium`, en `.gitignore`) |
| `reference_engine.py` + `reference_adapter.py` | `infrastructure/tiktok/tiktok_creator_source.py` (capa anticorrupción que devuelve un `Creator` del dominio) |
| `normalizer._counter_value` | `infrastructure/persistence/legacy_format.py` |
| `demo.py` | `infrastructure/persistence/capture_store.py` |
| Esquema de `benford_routes` | `interfaces/api/schemas.py` |
| Tabla de errores de `backend/main.py` | `interfaces/api/errors.py` |
| `manage.py` | `interfaces/cli/main.py` |

El motor es asíncrono: la CLI lo ejecuta con `asyncio.run` y la API lo corre en un único hilo de trabajo (un
solo perfil de Chromium, protegido por `filelock`).

## 4. Conciliación

### Big Five

Una sola llamada a Groq pide **puntaje y evidencia**, y el dominio decide qué se publica:

- Cada video se envía con una referencia corta `p1…p30`, para que el modelo no invente IDs.
- Por rasgo, Groq devuelve `score` (0–100) y `evidence: [{ref, quote}]`.
- Cada cita se comprueba con `canonical_text(quote) in canonical_text(descripción)`. Las que no aparecen
  literalmente se descartan.
- **Un `TraitScore` solo se publica si hay citas válidas de al menos 2 videos** (mismo umbral que
  `ocean_analysis`). Si no, `score: null` y `status: "insufficient_evidence"`.
- `evidenceCoverage` = 100 × videos con evidencia / videos analizados. Se muestra aparte y **nunca reemplaza al
  puntaje**: no tener señales no significa tener el rasgo bajo.
- Se elimina `normalizar_a_100`: los rasgos son independientes.

```json
"bigFiveProfile": {
  "summary": "Creador sociable y curioso...",
  "traits": [
    { "trait": "openness", "score": 78, "status": "scored", "evidenceCoverage": 40,
      "evidence": [ { "videoId": "7431234567890123456", "quote": "probando algo nuevo hoy" } ] },
    { "trait": "neuroticism", "score": null, "status": "insufficient_evidence",
      "evidenceCoverage": 4, "evidence": [] }
  ]
}
```

Cambios en el README: la regla 2 pasa a «`TraitScore` es un entero de 0 a 100, o nulo si no hay evidencia
suficiente»; se añade `TraitEvidence` al lenguaje ubicuo; en §14 se aclara que es una estimación a partir del texto,
no un test psicométrico. La app tiene que mostrar «Evidencia insuficiente» cuando `score` sea `null`.

### OrganicScore

- `analyze_values` se trasplanta sin cambios y recibe los valores de las **5 métricas de los 30 videos juntas**
  (hasta 150 valores).
- La política del dominio calcula `OrganicScore` solo si `expected_counts_sufficient` (110 valores válidos o más)
  y `orders_spanned >= 2`. Si no, `organicScore: null` con las `warnings` de media-scraper.
- Cuando se calcula: `round(100 × max(0, 1 − MAD / 0,03))`, como constante del dominio que el equipo puede ajustar.
- El `DISCLAIMER` llega hasta la app. Limitación conocida: las 5 métricas de un mismo video no son independientes;
  hay que decirlo en §14.
- Si hay muchas métricas nulas o en cero (por ejemplo, guardados ocultos), puede no llegarse a 110 valores aun
  con 30 videos; en ese caso el resultado es `null`, no se rellena.

## 5. Pruebas que se traen de media-scraper

Muchas pruebas de media-scraper dependen de Mongo, de OpenAI, de `scraper.py` o de `backend/main.py`. Solo se
traen **los casos que prueban código trasplantado**, cambiando únicamente los imports; los casos que dependen de
piezas no trasplantadas se omiten.

| Archivo de media-scraper | Qué se trae | Qué se omite |
|---|---|---|
| `tests/test_benford.py` | Casos de `analyze_values`, `benford_probabilities`, `first_significant_digit` | Casos de `benford_routes`, `BenfordRepository` y `main` (Mongo, FastAPI) |
| `tests/test_normalizer.py` | Casos de contadores abreviados que cubran `_counter_value` | Casos de `normalize_profile` |
| `tests/test_reference_engine.py` | Casos de `adapt_profile` y `reference_runtime` | Casos que usan `ProfileRepository`, `MemoryDatabase`, `main` o `scraper` |
| `tests/test_browser.py` | Casos de `session` que no dependan del bloqueo con `fcntl` | Los que dependen de `test_modes.sample_profile` si no se puede traer sin Mongo |
| `test_scraper.py`, `test_profile_posts.py`, `test_comments.py`, `test_ocean.py` y demás | — | Todo (prueban piezas que no se trasplantan) |

Partes que **quedan sin pruebas automáticas** por esta decisión: `Username`, `OrganicScore`, la comprobación de
citas, `TikTokCreatorSource`, el parche del motor, el bloqueo con `filelock`, el cliente de Groq y la API. Se
verifican a mano con la CLI y con perfiles reales.

## 6. Pasos (un commit cada uno)

Hasta el paso 9, `python main.py <usuario>` sigue usando el scraper actual. `main.py` y `analisis_bigfive.py`
mantienen sus funciones públicas (`scrape_tiktok_profile`, `analizar_perfil`, `obtener_api_key`) porque el
`app.py` de Jair las importa.

| # | Commit | Contenido | Verificación |
|---|---|---|---|
| 1 | `chore(backend): esqueleto de capas vacío` | `backend/pyproject.toml`, paquetes `truematch/...` con `__init__.py`, `backend/tests/` | `import truematch`; el pipeline no cambia |
| 2 | `chore(deps): fastapi, uvicorn, pydantic y filelock` | `requirements.txt` según §2 | `pip install -r requirements.txt` |
| 3 | `feat(domain): BenfordAnalyzer desde media-scraper` | `benford.py` tal cual + casos de `test_benford.py` | `python -m unittest` |
| 4 | `feat(domain): Username, Video, PublicProfile y Creator` | Regex unificada; `VideoStats` con `int` o `None` | Manual |
| 5 | `feat(domain): OrganicScore y AudienceAudit` | Mínimos (110 valores, 2 órdenes de magnitud), conversión de MAD a puntaje, `DISCLAIMER` | Manual |
| 6 | `feat(audience-audit): auditoría sobre los JSON existentes` | `legacy_format.py` con `_counter_value` + casos de `test_normalizer.py`; `AuditAudience`; comando `cli audit <usuario>` | `python -m unittest`; correr `cli audit` sobre `datos_*.json` |
| 7 | `feat(infrastructure): sesión persistente con filelock` | `session.py` adaptado, `cli session`, `.truematch/` en `.gitignore`; se retira `setup_cookies.py` | Linux **y** Windows a mano |
| 8 | `feat(infrastructure): integrar motor SCRAPINGTIKTOK (MIT)` | Motor + `runtime` + `LICENSE` + `PROVENANCE`; parche para saltar listas y comentarios; casos de `test_reference_engine.py` | `python -m unittest`; aún sin conectar |
| 9 | `feat(infrastructure): TikTokCreatorSource reemplaza al scraper` | Capa anticorrupción → `Creator`; 30 videos; repositorio JSON nuevo + `datos_<u>.json` heredado con enteros exactos (la web de Jair sigue leyendo `perfil.seguidores`); `scrape_tiktok_profile` queda como envoltorio; opción `--motor legado` durante una iteración | Ejecución real con 2–3 perfiles |
| 10 | `feat(persistence): capturas para modo demo` | `capture_store.py` + `cli capture --authorized` | Análisis completo sin TikTok |
| 11 | `feat(ai): Big Five con evidencia verificada` | Prompt con `p1…p30`; puntaje + citas; comprobación con `canonical_text`; `TraitScore` nulo; se borra `normalizar_a_100`; `analizar_perfil` mantiene su firma | Manual con perfiles reales |
| 12 | `feat(application): AnalyzeCreator` | Fuente → auditoría → personalidad → repositorio; la CLI lo usa | CLI de extremo a extremo |
| 13 | `feat(api): FastAPI con errores y esquemas de media-scraper` | Endpoints del plan de API; `audience-audit` con `warnings`, `disclaimer` y `ordersSpanned` | Manual con `uvicorn` |
| 14 | `docs: README §6.4, §7, §14 y créditos` | `TraitEvidence`, `TraitScore` nulo, límites de Benford, atribución MIT de SCRAPINGTIKTOK | — |

Después del paso 13 siguen sectores, match, propuestas y la migración de la web de Jair a FastAPI.
