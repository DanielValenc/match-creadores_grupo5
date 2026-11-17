"""Rutas de propuestas de colaboración para la app móvil.

    GET  /api/propuestas[?username=<usuario>]   historial (más recientes primero)
    POST /api/propuestas                        crea una propuesta (solo para creadores ya analizados)
    GET  /api/propuestas/<id>                   una propuesta
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
import uuid

from flask import Blueprint, current_app, jsonify, request

from truematch.domain.creator_profiling.username import InvalidUsername, Username
from truematch.infrastructure.config import load_settings
from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
from truematch.infrastructure.persistence.proposals_json_repository import JsonProposalRepository, ProposalStorageError

propuestas_bp = Blueprint("propuestas", __name__)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _error(message, status):
    return jsonify({"ok": False, "error": message}), status


def _repository():
    return JsonProposalRepository(load_settings().data_dir)


def _text(payload: dict[str, Any], key: str, limit: int) -> str:
    value = str(payload.get(key, "") or "").strip()
    if not value:
        raise ValueError(f"El campo '{key}' es obligatorio.")
    if len(value) > limit:
        raise ValueError(f"El campo '{key}' supera el máximo de {limit} caracteres.")
    return value


def _budget(raw) -> float | None:
    if raw in (None, ""):
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError("El presupuesto debe ser un número.")
    if raw < 0:
        raise ValueError("El presupuesto no puede ser negativo.")
    return round(float(raw), 2)


@propuestas_bp.get("/api/propuestas")
def listar_propuestas():
    creator = None
    if request.args.get("username", "").strip():
        try:
            creator = Username.parse(request.args["username"]).value
        except InvalidUsername:
            return _error("Nombre de usuario no válido.", 400)
    try:
        items = _repository().list(creator)
    except ProposalStorageError:
        current_app.logger.exception("No se pudo leer propuestas.json")
        return _error("No se pudo leer el historial de propuestas.", 500)
    return jsonify({"ok": True, "propuestas": items, "total": len(items)})


@propuestas_bp.post("/api/propuestas")
def crear_propuesta():
    payload = request.get_json(silent=True)
    payload = payload if isinstance(payload, dict) else {}
    try:
        username = Username.parse(str(payload.get("usuario_creador", "")))
    except InvalidUsername:
        return _error("El usuario de TikTok no es válido.", 400)

    # Solo se admite una propuesta para un creador que ya tenga un análisis guardado.
    if not LegacyJsonCreatorRepository(load_settings().data_dir).path_for(username).is_file():
        return _error("Primero debes analizar al creador antes de enviar una propuesta.", 409)

    try:
        correo = _text(payload, "correo_contacto", 150)
        if not EMAIL_RE.fullmatch(correo):
            raise ValueError("El correo de contacto no tiene un formato válido.")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        propuesta = {
            "id": str(uuid.uuid4()),
            "usuario_creador": username.value,
            "marca": _text(payload, "marca", 100),
            "correo_contacto": correo,
            "sector": _text(payload, "sector", 100),
            "campana": _text(payload, "campana", 120),
            "presupuesto": _budget(payload.get("presupuesto")),
            "mensaje": _text(payload, "mensaje", 3000),
            "estado": "pendiente",
            "created_at": now,
            "updated_at": now,
        }
    except ValueError as error:
        return _error(str(error), 400)

    try:
        _repository().add(propuesta)
    except ProposalStorageError:
        current_app.logger.exception("No se pudo guardar la propuesta")
        return _error("No se pudo guardar la propuesta.", 500)
    return jsonify({"ok": True, "propuesta": propuesta}), 201


@propuestas_bp.get("/api/propuestas/<proposal_id>")
def obtener_propuesta(proposal_id):
    try:
        propuesta = _repository().get(proposal_id)
    except ProposalStorageError:
        current_app.logger.exception("No se pudo leer propuestas.json")
        return _error("No se pudo leer el historial de propuestas.", 500)
    if propuesta is None:
        return _error("Propuesta no encontrada.", 404)
    return jsonify({"ok": True, "propuesta": propuesta})
