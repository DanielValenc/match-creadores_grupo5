"""
Análisis Big Five (OCEAN) de perfiles de TikTok usando la API de Groq.

Uso:
    python analisis_bigfive.py                       # pregunta el usuario
    python analisis_bigfive.py danielvalencia365     # por nombre de usuario
    python analisis_bigfive.py datos_ana.json        # por archivo
    python analisis_bigfive.py usuario1 usuario2     # varios a la vez
    python analisis_bigfive.py --todos               # todos los datos_*.json de la carpeta
    python analisis_bigfive.py --listar-modelos      # muestra los modelos disponibles en tu cuenta

Configuración (variables de entorno o archivo .env):
    GROQ_API_KEY   -> tu clave de Groq (obligatoria)
    GROQ_MODEL     -> modelo a usar (opcional)
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import sys

import requests

# Si está instalado python-dotenv, carga automáticamente el archivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# El paquete truematch vive en backend/. Si no se instaló con `pip install -e backend`, se añade a la ruta.
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from truematch.infrastructure.ai.groq_client import DEFAULT_MODEL, GroqClient, GroqError  # noqa: E402
from truematch.infrastructure.ai.groq_personality_analyzer import GroqPersonalityAnalyzer  # noqa: E402
from truematch.infrastructure.persistence.legacy_json_repository import personality_sections  # noqa: E402

MODELO_POR_DEFECTO = DEFAULT_MODEL  # el que funciona en tu cuenta
SIN_DESCRIPCION = "Sin descripción disponible"


def obtener_api_key():
    """Lee la API key desde la variable de entorno GROQ_API_KEY."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit(
            "Error: no se encontró la variable de entorno GROQ_API_KEY.\n"
            "  Windows (CMD):  set GROQ_API_KEY=tu_clave\n"
            "  Mac / Linux:    export GROQ_API_KEY=\"tu_clave\"\n"
            "  O crea un archivo .env con: GROQ_API_KEY=tu_clave"
        )
    return api_key


def listar_modelos(api_key):
    """Muestra los modelos a los que tiene acceso tu cuenta de Groq."""
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        r.raise_for_status()
        print("Modelos disponibles en tu cuenta:")
        for m in sorted(x["id"] for x in r.json().get("data", [])):
            print(f"  - {m}")
    except requests.RequestException as e:
        print(f"No se pudo obtener la lista de modelos: {e}")


def resolver_archivo(entrada):
    """Acepta 'usuario', '@usuario' o 'datos_usuario.json' y devuelve el nombre del archivo."""
    entrada = entrada.strip().lstrip("@")
    if entrada.lower().endswith(".json"):
        return entrada
    return f"datos_{entrada}.json"


def _video_id(video):
    """ID del video: el del motor nuevo, el de su enlace o, en el formato antiguo sin enlace, su posición."""
    if video.get("id"):
        return str(video["id"])
    match = re.search(r"/video/(\d+)", str(video.get("enlace", "")))
    return match.group(1) if match else f"posicion-{video.get('posicion', '?')}"


def _publicaciones(datos):
    """[(video_id, descripción)] de los videos con descripción, en su orden."""
    resultado = []
    for video in datos.get("videos_recientes", []):
        descripcion = str(video.get("descripcion") or "").strip()
        if descripcion and descripcion != SIN_DESCRIPCION:
            resultado.append((_video_id(video), descripcion))
    return resultado


def analizar_perfil(archivo_json, api_key=None, modelo=None):
    """Analiza un archivo JSON de perfil y guarda 'analisis_bigfive' dentro de él.
    Devuelve True si el análisis fue exitoso."""
    api_key = api_key or obtener_api_key()
    modelo = modelo or os.getenv("GROQ_MODEL", MODELO_POR_DEFECTO)

    print(f"\nLeyendo datos de {archivo_json}...")
    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {archivo_json}.")
        return False
    except json.JSONDecodeError:
        print(f"Error: {archivo_json} no es un JSON válido.")
        return False

    publicaciones = _publicaciones(datos)
    if not publicaciones:
        print("Error: el perfil no tiene descripciones de videos para analizar.")
        return False

    print(f"Enviando {len(publicaciones)} descripciones a Groq (modelo: {modelo})...")
    try:
        analisis = GroqPersonalityAnalyzer(GroqClient(api_key, modelo)).analyze_publications(publicaciones)
    except GroqError as e:
        print(e)
        return False
    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"Error procesando la respuesta de la IA: {e}")
        return False

    bigfive, evidencia, comercial = personality_sections(analisis)
    datos["analisis_bigfive"] = bigfive
    datos["analisis_bigfive_evidencia"] = evidencia
    datos["perfil_comercial"] = comercial
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

    print("¡Análisis completado exitosamente!")
    print(json.dumps({"analisis_bigfive": bigfive, "analisis_bigfive_evidencia": evidencia,
                      "perfil_comercial": comercial}, indent=4, ensure_ascii=False))
    return True


def main():
    parser = argparse.ArgumentParser(description="Análisis Big Five de perfiles de TikTok.")
    parser.add_argument("perfiles", nargs="*", help="Usuarios o archivos .json a analizar")
    parser.add_argument("--todos", action="store_true", help="Analiza todos los datos_*.json de la carpeta")
    parser.add_argument("--modelo", help="Modelo de Groq a utilizar")
    parser.add_argument("--listar-modelos", action="store_true", help="Muestra los modelos disponibles y sale")
    args = parser.parse_args()

    if args.listar_modelos:
        listar_modelos(obtener_api_key())
        return

    if args.todos:
        archivos = sorted(glob.glob("datos_*.json"))
    elif args.perfiles:
        archivos = [resolver_archivo(p) for p in args.perfiles]
    else:
        usuario = input("Usuario de TikTok o archivo .json a analizar: ")
        archivos = [resolver_archivo(usuario)]

    if not archivos:
        print("No se encontraron archivos datos_*.json para analizar.")
        return

    api_key = obtener_api_key()
    exitosos = sum(analizar_perfil(a, api_key, args.modelo) for a in archivos)
    print(f"\nResumen: {exitosos} de {len(archivos)} perfiles analizados correctamente.")


if __name__ == "__main__":
    main()