"""API Flask de Match Creadores: análisis de TikTok y gestión básica de propuestas."""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
load_dotenv(BASE_DIR / ".env")

from main import scrape_tiktok_profile  # noqa: E402
from analisis_bigfive import analizar_perfil, obtener_api_key  # noqa: E402

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

# El scraper comparte una sesión persistente de Chromium: solo una extracción a la vez.
SCRAPER_LOCK = threading.Lock()
PROPOSALS_LOCK = threading.Lock()
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{2,24}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PROPOSALS_FILE = BASE_DIR / "propuestas.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(payload: dict[str, Any], key: str, *, required: bool = True, limit: int = 200) -> str:
    value = str(payload.get(key, "") or "").strip()
    if required and not value:
        raise ValueError(f"El campo '{key}' es obligatorio.")
    if len(value) > limit:
        raise ValueError(f"El campo '{key}' supera el máximo de {limit} caracteres.")
    return value


def _load_proposals() -> list[dict[str, Any]]:
    if not PROPOSALS_FILE.exists():
        return []
    with PROPOSALS_FILE.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, list):
        raise ValueError("El archivo propuestas.json no contiene una lista válida.")
    return data


def _save_proposals(proposals: list[dict[str, Any]]) -> None:
    """Escribe de forma atómica para evitar dejar propuestas.json incompleto."""
    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        dir=PROPOSALS_FILE.parent,
        prefix=".propuestas.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(proposals, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, PROPOSALS_FILE)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


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
            "error": "Ingresa un usuario válido de TikTok, sin espacios ni URL. Ejemplo: @usuario",
        }), 400

    try:
        api_key = obtener_api_key()
    except SystemExit as exc:
        return jsonify({
            "ok": False,
            "error": str(exc) or "No se encontró GROQ_API_KEY en el archivo .env.",
        }), 503

    if not SCRAPER_LOCK.acquire(blocking=False):
        return jsonify({
            "ok": False,
            "error": "Ya hay otra extracción en curso. Espera a que termine antes de iniciar otra.",
        }), 409

    try:
        app.logger.info("Iniciando extracción para @%s", username)
        archivo = scrape_tiktok_profile(username)
        if not archivo:
            return jsonify({
                "ok": False,
                "error": (
                    "No se pudieron extraer los datos del perfil. TikTok pudo mostrar un CAPTCHA, "
                    "cambiar su estructura o bloquear temporalmente la solicitud. Revisa Chromium "
                    "y la consola del servidor."
                ),
            }), 502

        archivo_path = Path(archivo)
        if not archivo_path.is_absolute():
            archivo_path = BASE_DIR / archivo_path
        if not archivo_path.is_file():
            return jsonify({
                "ok": False,
                "error": f"El scraper terminó, pero no se encontró el archivo generado: {archivo_path.name}",
            }), 500

        app.logger.info("Ejecutando análisis Big Five para @%s", username)
        try:
            analisis_ok = analizar_perfil(str(archivo_path), api_key=api_key)
        except SystemExit as exc:
            return jsonify({
                "ok": False,
                "error": str(exc) or "Falló la configuración del análisis de IA.",
            }), 503

        if not analisis_ok:
            return jsonify({
                "ok": False,
                "error": (
                    "La extracción se completó, pero Groq no pudo generar el análisis. "
                    "Revisa GROQ_MODEL, GROQ_API_KEY, la conexión y las descripciones de los videos."
                ),
            }), 502

        with archivo_path.open("r", encoding="utf-8") as stream:
            datos = json.load(stream)
        return jsonify({"ok": True, "datos": datos})

    except Exception as exc:
        app.logger.exception("Error procesando @%s", username)
        return jsonify({
            "ok": False,
            "error": f"Ocurrió un error durante el procesamiento: {type(exc).__name__}: {exc}",
        }), 500
    finally:
        SCRAPER_LOCK.release()


@app.get("/api/creadores/<username>")
def obtener_creador(username: str):
    """Devuelve un análisis ya guardado sin volver a ejecutar Playwright ni Groq."""
    username = username.strip().lstrip("@")
    if not USERNAME_RE.fullmatch(username) or username in {".", ".."}:
        return jsonify({"ok": False, "error": "Nombre de usuario no válido."}), 400

    path = BASE_DIR / f"datos_{username}.json"
    if not path.is_file():
        return jsonify({"ok": False, "error": "No existe un análisis guardado para ese creador."}), 404

    try:
        with path.open("r", encoding="utf-8") as stream:
            return jsonify({"ok": True, "datos": json.load(stream)})
    except (OSError, json.JSONDecodeError):
        app.logger.exception("No se pudo leer el análisis de @%s", username)
        return jsonify({"ok": False, "error": "No se pudo leer el análisis guardado."}), 500


@app.get("/api/creadores")
def listar_creadores():
    """Lista los análisis JSON disponibles para crear una sección de historial en la app."""
    items: list[dict[str, Any]] = []
    for path in BASE_DIR.glob("datos_*.json"):
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
            profile = data.get("perfil") or {}
            audit = data.get("auditoria_audiencia") or {}
            items.append({
                "usuario": data.get("usuario") or path.stem.removeprefix("datos_"),
                "foto_perfil": profile.get("foto_perfil"),
                "seguidores": profile.get("seguidores"),
                "puntaje_organico": audit.get("puntaje_organico"),
                "actualizado": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            })
        except (OSError, json.JSONDecodeError, AttributeError):
            app.logger.warning("Se omitió un archivo de análisis inválido: %s", path.name)
    items.sort(key=lambda item: item["actualizado"], reverse=True)
    return jsonify({"ok": True, "creadores": items, "total": len(items)})


@app.route("/api/propuestas", methods=["GET", "POST"])
def propuestas():
    if request.method == "GET":
        username_filter = request.args.get("username", "").strip().lstrip("@")
        with PROPOSALS_LOCK:
            try:
                items = _load_proposals()
            except (OSError, json.JSONDecodeError, ValueError):
                app.logger.exception("No se pudo leer propuestas.json")
                return jsonify({"ok": False, "error": "No se pudo leer el historial de propuestas."}), 500
        if username_filter:
            items = [p for p in items if p.get("usuario_creador") == username_filter]
        items.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return jsonify({"ok": True, "propuestas": items, "total": len(items)})

    payload: dict[str, Any] = request.get_json(silent=True) or {}
    try:
        username = _text(payload, "usuario_creador", limit=24).lstrip("@").strip()
        if not USERNAME_RE.fullmatch(username) or username in {".", ".."}:
            raise ValueError("El usuario de TikTok no es válido.")

        # La propuesta solo se admite para un creador que ya tenga un análisis local guardado.
        creator_file = BASE_DIR / f"datos_{username}.json"
        if not creator_file.is_file():
            return jsonify({
                "ok": False,
                "error": "Primero debes analizar al creador antes de enviar una propuesta.",
            }), 409

        marca = _text(payload, "marca", limit=100)
        correo = _text(payload, "correo_contacto", limit=150)
        if not EMAIL_RE.fullmatch(correo):
            raise ValueError("El correo de contacto no tiene un formato válido.")
        sector = _text(payload, "sector", limit=100)
        campana = _text(payload, "campana", limit=120)
        mensaje = _text(payload, "mensaje", limit=3000)

        raw_budget = payload.get("presupuesto")
        presupuesto: float | None = None
        if raw_budget not in (None, ""):
            if isinstance(raw_budget, bool) or not isinstance(raw_budget, (int, float)):
                raise ValueError("El presupuesto debe ser un número.")
            if raw_budget < 0:
                raise ValueError("El presupuesto no puede ser negativo.")
            presupuesto = round(float(raw_budget), 2)

    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    now = _utc_now()
    propuesta = {
        "id": str(uuid.uuid4()),
        "usuario_creador": username,
        "marca": marca,
        "correo_contacto": correo,
        "sector": sector,
        "campana": campana,
        "presupuesto": presupuesto,
        "mensaje": mensaje,
        "estado": "pendiente",
        "created_at": now,
        "updated_at": now,
    }

    with PROPOSALS_LOCK:
        try:
            items = _load_proposals()
            items.append(propuesta)
            _save_proposals(items)
        except (OSError, json.JSONDecodeError, ValueError):
            app.logger.exception("No se pudo guardar la propuesta")
            return jsonify({"ok": False, "error": "No se pudo guardar la propuesta."}), 500

    return jsonify({"ok": True, "propuesta": propuesta}), 201


@app.get("/api/propuestas/<proposal_id>")
def obtener_propuesta(proposal_id: str):
    with PROPOSALS_LOCK:
        try:
            items = _load_proposals()
        except (OSError, json.JSONDecodeError, ValueError):
            app.logger.exception("No se pudo leer propuestas.json")
            return jsonify({"ok": False, "error": "No se pudo leer el historial de propuestas."}), 500
    propuesta = next((p for p in items if p.get("id") == proposal_id), None)
    if propuesta is None:
        return jsonify({"ok": False, "error": "Propuesta no encontrada."}), 404
    return jsonify({"ok": True, "propuesta": propuesta})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\nMATCH CREADORES - API local")
    print("Web: http://127.0.0.1:5000")
    print("API: http://<IP-DE-TU-PC>:5000/api/health\n")
    # 0.0.0.0 permite que el teléfono de la misma red Wi-Fi llegue al backend.
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
