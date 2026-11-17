"""Web local de TrueMatch AI (Flask): formulario, extracción de TikTok y análisis.

Levantar (desde backend/):  python -m truematch.interfaces.cli.main web
La página y la app móvil reciben en /api/analizar el mismo documento que se guarda en datos_<usuario>.json, y en
/api/datos/<usuario> el que ya está guardado. /api/creadores lista los análisis guardados y /api/propuestas
(interfaces/web/proposals.py) gestiona las propuestas. Con /?usuario=<usuario> la página carga un resultado guardado.

Modo de scrapeo: lo decide el comando `web` de la CLI y se pasa por la variable de entorno
TRUEMATCH_SCRAPE_HEADLESS ("1" = sesión guardada/headless, "0" = captcha manual/Chromium visible).
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import socket
from typing import Any

from flask import Flask, jsonify, render_template, request

from truematch.application.use_cases.analyze_creator import AnalyzeCreator
from truematch.domain.audience_audit.organic_score import MIN_ORDERS_SPANNED, MIN_VALID_VALUES
from truematch.domain.creator_profiling.big_five import MIN_SUPPORTING_VIDEOS
from truematch.domain.creator_profiling.username import InvalidUsername, Username
from truematch.infrastructure.ai.groq_client import GroqClient
from truematch.infrastructure.ai.groq_personality_analyzer import GroqPersonalityAnalyzer
from truematch.infrastructure.config import ConfigError, load_settings
from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository, legacy_document
from truematch.infrastructure.tiktok.runtime import AccessRestricted, IdentityError
from truematch.infrastructure.tiktok.session import SessionBusyError
from truematch.infrastructure.tiktok.tiktok_creator_source import TikTokCreatorSource
from truematch.interfaces.web.proposals import propuestas_bp

SESSION_COMMAND = "python -m truematch.interfaces.cli.main session"

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # Un username o una propuesta (mensaje de hasta 3000 caracteres).
app.register_blueprint(propuestas_bp)


def error(message, status):
    return jsonify({"ok": False, "error": message}), status


def build_use_case():
    """Arma AnalyzeCreator con la configuración actual. Lanza ConfigError si falta GROQ_API_KEY."""
    settings = load_settings()
    analyzer = GroqPersonalityAnalyzer(GroqClient(settings.require_groq_api_key(), settings.groq_model))
    # La CLI pone TRUEMATCH_SCRAPE_HEADLESS a "1" (sesión guardada) o "0" (captcha manual).
    # Sin la variable, se asume sesión guardada (comportamiento histórico).
    headless = os.getenv("TRUEMATCH_SCRAPE_HEADLESS", "1") == "1"
    return AnalyzeCreator(
        TikTokCreatorSource(headless=headless),
        LegacyJsonCreatorRepository(settings.data_dir),
        analyzer,
    )


@app.get("/")
def inicio():
    # Los mínimos vienen del dominio para que la página explique por qué falta un puntaje.
    return render_template("index.html", min_valid_values=MIN_VALID_VALUES, min_orders_spanned=MIN_ORDERS_SPANNED,
                           min_supporting_videos=MIN_SUPPORTING_VIDEOS)


@app.get("/api/datos/<usuario>")
def datos_guardados(usuario):
    """Resultado ya guardado en datos_<usuario>.json, sin TikTok ni Groq (misma forma que /api/analizar)."""
    try:
        username = Username.parse(usuario)
    except InvalidUsername:
        return error("Ingresa un usuario válido de TikTok, sin espacios ni URL. Ejemplo: @usuario", 400)
    path = LegacyJsonCreatorRepository(load_settings().data_dir).path_for(username)
    if not path.is_file():
        return error(f"No hay resultados guardados de @{username}. Analízalo primero desde esta página.", 404)
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        app.logger.exception("No se pudo leer %s", path)
        return error(f"No se pudieron leer los resultados guardados de @{username}.", 500)
    return jsonify({"ok": True, "datos": datos})


@app.get("/api/creadores")
def listar_creadores():
    """Análisis guardados (datos_<usuario>.json), del más reciente al más antiguo: historial de la app móvil."""
    items: list[dict[str, Any]] = []
    for path in load_settings().data_dir.glob("datos_*.json"):
        try:
            datos = json.loads(path.read_text(encoding="utf-8"))
            perfil = datos.get("perfil") or {}
            auditoria = datos.get("auditoria_audiencia") or {}
            items.append({
                "usuario": datos.get("usuario") or path.stem.removeprefix("datos_"),
                "foto_perfil": perfil.get("foto_perfil"),
                "seguidores": perfil.get("seguidores"),
                "puntaje_organico": auditoria.get("puntaje_organico"),
                "actualizado": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            })
        except (OSError, ValueError, AttributeError):
            app.logger.warning("Se omitió un archivo de análisis inválido: %s", path.name)
    items.sort(key=lambda item: item["actualizado"], reverse=True)
    return jsonify({"ok": True, "creadores": items, "total": len(items)})


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "servicio": "Match Creadores"})


@app.post("/api/analizar")
def analizar_usuario():
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    try:
        username = Username.parse(str(payload.get("username", "")))
    except InvalidUsername:
        return error("Ingresa un usuario válido de TikTok, sin espacios ni URL. Ejemplo: @usuario", 400)

    # La clave se comprueba antes de abrir Chromium y empezar la extracción.
    try:
        use_case = build_use_case()
    except ConfigError as exc:
        return error(str(exc), 503)

    try:
        app.logger.info("Analizando @%s", username)
        result = use_case.execute(username)
    except SessionBusyError:
        return error("Ya hay otra extracción en curso. Espera a que termine antes de iniciar otra.", 409)
    except AccessRestricted as exc:
        return error(f"TikTok pidió verificación o inicio de sesión. {exc}", 502)
    except IdentityError:
        return error("Los datos obtenidos no corresponden al usuario solicitado. Intenta de nuevo.", 502)
    except (RuntimeError, ValueError):
        return error(
            "No se pudieron extraer los datos del perfil. TikTok pudo pedir verificación, cambiar su estructura "
            f"o bloquear temporalmente la solicitud. Inicia sesión de nuevo con: {SESSION_COMMAND} "
            "y revisa la consola del servidor.",
            502,
        )
    except Exception as exc:  # Evita que un error inesperado cierre el servidor web.
        app.logger.exception("Error procesando @%s", username)
        return error(f"Ocurrió un error durante el procesamiento: {type(exc).__name__}: {exc}", 500)

    if result.personality_error:
        app.logger.warning("Groq no generó el análisis de @%s: %s", username, result.personality_error)
        return error(
            "La extracción se completó, pero Groq no pudo generar el análisis. "
            "Revisa GROQ_MODEL, tu API key, la conexión y que los videos tengan descripciones. "
            "Consulta también la consola del servidor para ver el error técnico.",
            502,
        )

    return jsonify({"ok": True, "datos": legacy_document(result.creator, result.audit, result.personality)})


def lan_ip():
    """IP de la PC en la red local, la que debe usar el teléfono (no envía ningún paquete)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.255.255.255", 1))
            return sock.getsockname()[0]
    except OSError:
        return "<IP-DE-TU-PC>"


def run(host="0.0.0.0", port=5000)::
    logging.basicConfig(level=logging.INFO)
    visible_en_red = host in ("0.0.0.0", "::")
    use_session = os.getenv("TRUEMATCH_SCRAPE_HEADLESS", "1") == "1"
    modo = "sesión guardada (headless)" if use_session else "captcha manual (Chromium visible)"
    print("\nMATCH CREADORES - API local")
    print(f"Web: http://{'127.0.0.1' if visible_en_red else host}:{port}")
    if visible_en_red:
        print(f"API (teléfono, misma Wi-Fi): http://{lan_ip()}:{port}/api/health")
        print("Visible en tu red local y sin autenticación: usa --host 127.0.0.1 para limitarla a esta PC.")
    print(f"Modo de scrapeo: {modo}.")
    if use_session:
        print(f"Si la sesión caduca, iníciala de nuevo con: {SESSION_COMMAND}")
    else:
        print("Cada extracción abrirá Chromium visible para resolver el captcha a mano.")
    print()
    app.run(host=host, port=port, debug=False, threaded=True)