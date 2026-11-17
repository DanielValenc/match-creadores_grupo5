"""
Extracción de datos de un perfil de TikTok y análisis Big Five.

Uso:
    python main.py                      # pregunta el usuario
    python main.py danielvalencia365    # usuario por argumento
    python main.py usuario --sin-analisis   # solo extrae, no analiza
"""
import argparse
import json
import logging
import os
from pathlib import Path
import sys

# El paquete truematch vive en backend/. Si no se instaló con `pip install -e backend`, se añade a la ruta.
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _analizador_groq():
    """Analizador de personalidad con la clave y el modelo de siempre. Si falta GROQ_API_KEY, termina el
    programa antes de abrir TikTok (SystemExit de obtener_api_key)."""
    from analisis_bigfive import MODELO_POR_DEFECTO, obtener_api_key
    from truematch.infrastructure.ai.groq_client import GroqClient
    from truematch.infrastructure.ai.groq_personality_analyzer import GroqPersonalityAnalyzer

    return GroqPersonalityAnalyzer(GroqClient(obtener_api_key(), os.getenv("GROQ_MODEL", MODELO_POR_DEFECTO)))


def analizar_creador(username, analizador=None):
    """Caso de uso AnalyzeCreator con el motor SCRAPINGTIKTOK: fuente → auditoría → personalidad (si hay
    analizador) → datos_<usuario>.json. Devuelve el AnalysisResult o None si falla la extracción."""
    print(f"\nIniciando extracción para: @{username.strip().lstrip('@')} (motor SCRAPINGTIKTOK, hasta 30 videos)")
    try:
        # Import diferido: --help funciona aunque falte alguna dependencia (Playwright, filelock).
        from truematch.application.use_cases.analyze_creator import AnalyzeCreator
        from truematch.domain.creator_profiling.username import Username
        from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
        from truematch.infrastructure.tiktok.tiktok_creator_source import TikTokCreatorSource

        caso_de_uso = AnalyzeCreator(TikTokCreatorSource(), LegacyJsonCreatorRepository("."), analizador)
        resultado = caso_de_uso.execute(Username.parse(username))
    except Exception as e:
        print("\nError: no se pudo extraer el perfil.")
        print(f"Detalle: {e}")
        print("Si TikTok pide verificación o inicio de sesión, ejecuta desde backend/: "
              "python -m truematch.interfaces.cli.main session")
        return None

    print(f"\n¡ÉXITO! Se extrajeron {len(resultado.creator.videos)} videos. Archivo: {resultado.location}")
    return resultado


def scrape_tiktok_profile(username):
    """Extrae el perfil con el motor SCRAPINGTIKTOK, audita la audiencia y guarda datos_<usuario>.json.
    Devuelve el nombre del archivo o None si falla (misma firma y contrato que el scraper anterior)."""
    resultado = analizar_creador(username)
    return resultado.location if resultado else None


def _numero(valor):
    """Entero con separador de miles; '—' si se desconoce. Los textos de archivos antiguos ("1.2M") se muestran tal cual."""
    if valor is None:
        return "—"
    if isinstance(valor, int) and not isinstance(valor, bool):
        return f"{valor:,}".replace(",", ".")
    return str(valor)


def imprimir_resumen(archivo):
    """Resumen legible de datos_<usuario>.json: una línea de perfil y una tabla con una fila por video."""
    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)
    perfil = datos.get("perfil", {})
    print(f"\nPerfil @{datos.get('usuario', '?')}: {_numero(perfil.get('seguidores'))} seguidores · "
          f"{_numero(perfil.get('siguiendo'))} siguiendo · {_numero(perfil.get('me_gusta'))} me gusta")

    columnas = ("#", "Fecha", "Vistas", "Likes", "Coment.", "Compart.", "Guard.", "Descripción")
    filas = []
    for video in datos.get("videos_recientes", []):
        fecha = (video.get("fecha_publicacion") or "")[:10] or "—"
        descripcion = " ".join(str(video.get("descripcion") or "").split())
        if len(descripcion) > 40:
            descripcion = descripcion[:39] + "…"
        filas.append((str(video.get("posicion", "")), fecha,
                      *(_numero(video.get(k)) for k in ("vistas", "me_gusta", "comentarios", "compartidos", "guardados")),
                      descripcion))
    anchos = [max(len(columnas[i]), *(len(fila[i]) for fila in filas)) if filas else len(columnas[i])
              for i in range(len(columnas))]

    def linea(celdas):
        # Números alineados a la derecha (columnas 0 y 2-6); fecha y descripción a la izquierda.
        return "  ".join(c.rjust(anchos[i]) if i in (0, 2, 3, 4, 5, 6) else c.ljust(anchos[i])
                         for i, c in enumerate(celdas)).rstrip()

    print(linea(columnas))
    print(linea(tuple("-" * a for a in anchos)))
    for fila in filas:
        print(linea(fila))
    print(f"{len(filas)} videos")


def main():
    parser = argparse.ArgumentParser(description="Extrae datos de TikTok y analiza Big Five.")
    parser.add_argument("usuario", nargs="?", help="Username de TikTok (sin @)")
    parser.add_argument("--sin-analisis", action="store_true", help="Solo extraer, sin análisis Big Five")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    usuario = args.usuario or input("Ingresa el username de TikTok (sin el @): ")
    usuario = usuario.strip().lstrip("@")

    analizador = None if args.sin_analisis else _analizador_groq()
    resultado = analizar_creador(usuario, analizador)
    if not resultado:
        return
    imprimir_resumen(resultado.location)
    from truematch.interfaces.cli.formatting import audit_line, personality_line
    if resultado.personality:
        print(f"\n{personality_line(resultado.personality)}")
    elif resultado.personality_error:
        print(f"\nAnálisis de personalidad no completado: {resultado.personality_error}")
    print(f"\n{audit_line(resultado.audit)}")


if __name__ == "__main__":
    main()