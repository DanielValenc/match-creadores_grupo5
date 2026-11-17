"""Aplicación web local para integrar el scraper de TikTok y el análisis Big Five.

Coloca este archivo en la raíz del repositorio, junto a main.py y
analisis_bigfive.py. Ejecuta: python app.py
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Todos los archivos JSON y la sesión de Playwright quedan en la raíz del repo,
# independientemente de desde qué carpeta se invoque `python ruta\\app.py`.
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
load_dotenv(BASE_DIR / ".env")

from main import scrape_tiktok_profile  # noqa: E402
from analisis_bigfive import analizar_perfil, obtener_api_key  # noqa: E402

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024  # El endpoint solo recibe un username.

# El motor usa una única sesión persistente de Chromium (.truematch/chromium).
# No se deben ejecutar dos extracciones simultáneamente sobre esa misma sesión.
SCRAPER_LOCK = threading.Lock()
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{2,24}$")


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "servicio": "Match Creadores"})


@app.post("/api/analizar")
def analizar_usuario():
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip().lstrip("@").strip()

    if not username or not USERNAME_RE.fullmatch(username) or username in {".", ".."}:
        return jsonify({
            "ok": False,
            "error": "Ingresa un usuario válido de TikTok, sin espacios ni URL. Ejemplo: @usuario"
        }), 400

    # Comprobar la clave antes de abrir Chromium y empezar el scraping.
    try:
        api_key = obtener_api_key()
    except SystemExit as exc:
        return jsonify({
            "ok": False,
            "error": str(exc) or "No se encontró GROQ_API_KEY en el archivo .env."
        }), 503

    if not SCRAPER_LOCK.acquire(blocking=False):
        return jsonify({
            "ok": False,
            "error": "Ya hay otra extracción en curso. Espera a que termine antes de iniciar otra."
        }), 409

    try:
        app.logger.info("Iniciando extracción para @%s", username)
        archivo = scrape_tiktok_profile(username)
        if not archivo:
            return jsonify({
                "ok": False,
                "error": (
                    "No se pudieron extraer los datos del perfil. TikTok pudo mostrar un CAPTCHA, "
                    "cambiar su estructura o bloquear temporalmente la solicitud. Revisa la ventana "
                    "de Chromium y la consola del servidor."
                )
            }), 502

        archivo_path = Path(archivo)
        if not archivo_path.is_absolute():
            archivo_path = BASE_DIR / archivo_path
        if not archivo_path.is_file():
            return jsonify({
                "ok": False,
                "error": f"El scraper terminó, pero no se encontró el archivo generado: {archivo_path.name}"
            }), 500

        app.logger.info("Ejecutando análisis Big Five para @%s", username)
        try:
            analisis_ok = analizar_perfil(str(archivo_path), api_key=api_key)
        except SystemExit as exc:
            return jsonify({"ok": False, "error": str(exc) or "Falló la configuración del análisis de IA."}), 503

        if not analisis_ok:
            return jsonify({
                "ok": False,
                "error": (
                    "La extracción se completó, pero Groq no pudo generar el análisis. "
                    "Revisa GROQ_MODEL, tu API key, la conexión y que los videos tengan descripciones. "
                    "Consulta también la consola del servidor para ver el error técnico."
                )
            }), 502

        with archivo_path.open("r", encoding="utf-8") as file:
            datos = json.load(file)

        return jsonify({"ok": True, "datos": datos})

    except Exception as exc:  # Evita que un error de Playwright cierre el servidor web.
        app.logger.exception("Error procesando @%s", username)
        return jsonify({
            "ok": False,
            "error": f"Ocurrió un error durante el procesamiento: {type(exc).__name__}: {exc}"
        }), 500
    finally:
        SCRAPER_LOCK.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\nMATCH CREADORES - Dashboard local")
    print("Abre http://127.0.0.1:5000 en tu navegador.")
    print("La extracción abre Chromium en este mismo equipo.\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
