"""
Extracción de datos de un perfil de TikTok y análisis Big Five.

Uso:
    python main.py                      # pregunta el usuario
    python main.py danielvalencia365    # usuario por argumento
    python main.py usuario --sin-analisis   # solo extrae, no analiza
    python main.py usuario --motor legado   # usa el scraper anterior (temporal)
"""
import argparse
import json
import logging
from pathlib import Path
import sys
import time

from playwright.sync_api import sync_playwright

PLACEHOLDER_FOTO = "https://via.placeholder.com/150?text=Sin+Foto"
PLACEHOLDER_VIDEO = "https://via.placeholder.com/300x400?text=Video"
SIN_DESCRIPCION = "Sin descripción disponible"
MAX_VIDEOS = 10

# El paquete truematch vive en backend/. Si no se instaló con `pip install -e backend`, se añade a la ruta.
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def scrape_tiktok_profile(username):
    """Extrae el perfil con el motor SCRAPINGTIKTOK y guarda datos_<usuario>.json.
    Devuelve el nombre del archivo o None si falla (misma firma y contrato que el scraper anterior)."""
    print(f"\nIniciando extracción para: @{username.strip().lstrip('@')} (motor SCRAPINGTIKTOK, hasta 30 videos)")
    try:
        # Import diferido: --motor legado sigue funcionando aunque falte alguna dependencia nueva.
        from truematch.domain.creator_profiling.username import Username
        from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
        from truematch.infrastructure.tiktok.tiktok_creator_source import TikTokCreatorSource

        creator = TikTokCreatorSource().fetch(Username.parse(username))
        nombre_archivo = str(LegacyJsonCreatorRepository(".").save(creator))
    except Exception as e:
        print("\nError: no se pudo extraer el perfil con el motor nuevo.")
        print(f"Detalle: {e}")
        print("Si TikTok pide verificación o inicio de sesión, ejecuta desde backend/: "
              "python -m truematch.interfaces.cli.main session")
        return None

    print(f"\n¡ÉXITO! Se extrajeron {len(creator.videos)} videos. Archivo: {nombre_archivo}")
    return nombre_archivo


def scrape_tiktok_profile_legado(username):
    """Scraper anterior (sin cambios). Extrae el perfil y guarda datos_<usuario>.json.
    Devuelve el nombre del archivo o None si falla."""
    print(f"\nIniciando extracción para: @{username}")

    datos_descarga = {"usuario": username, "perfil": {}, "videos_recientes": []}
    nombre_archivo = None

    with sync_playwright() as p:
        # Carpeta local que guarda cookies/sesión para reducir Captchas
        context = p.chromium.launch_persistent_context(
            user_data_dir="perfil_tiktok",
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.pages[0]

        try:
            page.goto(f"https://www.tiktok.com/@{username}", wait_until="domcontentloaded", timeout=60000)
            print("Verificando conexión...")
            time.sleep(4)

            print("Extrayendo estadísticas principales y foto de perfil...")
            # Espera hasta 60 s por si aparece un Captcha inicial
            page.wait_for_selector('strong[title="Seguidores"]', timeout=60000)

            siguiendo = page.locator('strong[title="Siguiendo"]').text_content()
            seguidores = page.locator('strong[title="Seguidores"]').text_content()
            likes = page.locator('strong[title="Me gusta"]').text_content()

            try:
                foto_perfil = page.locator('img[class*="Avatar"]').first.get_attribute("src", timeout=5000)
            except Exception:
                foto_perfil = PLACEHOLDER_FOTO

            datos_descarga["perfil"] = {
                "foto_perfil": foto_perfil,
                "siguiendo": siguiendo,
                "seguidores": seguidores,
                "me_gusta": likes,
            }

            print("Haciendo scroll simulado para cargar las publicaciones...")
            for _ in range(4):
                page.mouse.wheel(0, 800)
                time.sleep(1.5)

            print("Capturando los enlaces y descripciones de los videos...")
            page.wait_for_selector('a[href*="/video/"]', timeout=60000)
            videos_links = page.locator('a[href*="/video/"]')

            videos_extraidos = {}  # evita duplicados
            for i in range(videos_links.count()):
                elemento = videos_links.nth(i)
                href = elemento.get_attribute("href")
                if not href or "/video/" not in href:
                    continue
                if href.startswith("/"):
                    href = "https://www.tiktok.com" + href
                if href in videos_extraidos:
                    continue

                try:
                    img = elemento.locator("img").first
                    miniatura = img.get_attribute("src", timeout=2000)
                    descripcion = img.get_attribute("alt", timeout=2000)
                except Exception:
                    miniatura, descripcion = PLACEHOLDER_VIDEO, SIN_DESCRIPCION

                videos_extraidos[href] = {
                    "miniatura": miniatura,
                    "descripcion": descripcion or SIN_DESCRIPCION,
                }

            for i, (enlace, v) in enumerate(list(videos_extraidos.items())[:MAX_VIDEOS]):
                datos_descarga["videos_recientes"].append({
                    "posicion": i + 1,
                    "enlace": enlace,
                    "miniatura": v["miniatura"],
                    "descripcion": v["descripcion"],
                    "estado": "Extraído exitosamente",
                })

            nombre_archivo = f"datos_{username}.json"
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                json.dump(datos_descarga, f, ensure_ascii=False, indent=4)

            print(f"\n¡ÉXITO! Se extrajeron {len(datos_descarga['videos_recientes'])} videos. Archivo: {nombre_archivo}")

        except Exception as e:
            print("\nError: TikTok bloqueó la conexión o saltó un Captcha. "
                  "Borra la carpeta 'perfil_tiktok', espera unos minutos y reintenta.")
            print(f"Detalle técnico: {e}")
            nombre_archivo = None

        finally:
            context.close()

    return nombre_archivo


def _numero(valor):
    """Entero con separador de miles; '—' si se desconoce. Los textos del scraper legado se muestran tal cual."""
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
    parser.add_argument("--motor", choices=["nuevo", "legado"], default="nuevo",
                        help="nuevo: SCRAPINGTIKTOK (por defecto); legado: scraper anterior")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    usuario = args.usuario or input("Ingresa el username de TikTok (sin el @): ")
    usuario = usuario.strip().lstrip("@")

    if args.motor == "legado":
        archivo = scrape_tiktok_profile_legado(usuario)
    else:
        archivo = scrape_tiktok_profile(usuario)

    if archivo:
        imprimir_resumen(archivo)

    if archivo and not args.sin_analisis:
        # Se importa aquí para no exigir GROQ_API_KEY si solo se quiere extraer
        from analisis_bigfive import analizar_perfil
        analizar_perfil(archivo)


if __name__ == "__main__":
    main()