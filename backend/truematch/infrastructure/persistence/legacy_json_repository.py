"""Repositorio JSON en el formato heredado datos_<usuario>.json.

Mantiene las claves que lee la web (usuario, perfil.*, videos_recientes[].*) y añade,
por video, id, fecha_publicacion y las cinco métricas. Los contadores son enteros exactos o null (desconocido),
nunca textos abreviados como "1.2M". Las secciones de resultados son analisis_bigfive,
analisis_bigfive_evidencia, perfil_comercial y auditoria_audiencia.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile

from truematch.application.ports.creator_repository import CreatorRepository
from truematch.domain.audience_audit.audience_audit import AudienceAudit
from truematch.domain.creator_profiling.big_five import MIN_SUPPORTING_VIDEOS
from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.personality_analysis import PersonalityAnalysis
from truematch.domain.creator_profiling.public_profile import PublicProfile
from truematch.domain.creator_profiling.username import Username
from truematch.domain.creator_profiling.video import Video, VideoStats
from truematch.infrastructure.ai.prompts import LEGACY_TRAIT_KEYS

PLACEHOLDER_FOTO = "https://via.placeholder.com/150?text=Sin+Foto"
PLACEHOLDER_VIDEO = "https://via.placeholder.com/300x400?text=Video"
SIN_DESCRIPCION = "Sin descripción disponible"
# Claves heredadas de cada métrica, en el orden de VideoStats.values().
METRIC_KEYS = ("vistas", "me_gusta", "comentarios", "compartidos", "guardados")


def to_legacy_dict(creator: Creator):
    profile = creator.profile
    return {
        "usuario": creator.username.value,
        "perfil": {
            "foto_perfil": profile.avatar_url or PLACEHOLDER_FOTO,
            "siguiendo": profile.following,
            "seguidores": profile.followers,
            "me_gusta": profile.likes,
        },
        "videos_recientes": [
            {
                "posicion": position,
                "enlace": video.url,
                "miniatura": video.thumbnail_url or PLACEHOLDER_VIDEO,
                "descripcion": video.description.strip() if video.has_description() else SIN_DESCRIPCION,
                "estado": "Extraído exitosamente",
                "id": video.id,
                "fecha_publicacion": video.published_at.isoformat() if video.published_at else None,
                **dict(zip(METRIC_KEYS, video.stats.values())),
            }
            for position, video in enumerate(creator.videos, start=1)
        ],
    }


def audit_section(audit: AudienceAudit):
    """Clave auditoria_audiencia: puntaje o null, muestra, distribución por dígito, advertencias y disclaimer."""
    analysis = audit.analysis
    return {
        "puntaje_organico": audit.organic_score.value if audit.organic_score else None,
        "metricas": list(METRIC_KEYS),
        "tamano_muestra": analysis["valid_records"],
        "registros_totales": analysis["total_records"],
        "excluidos": dict(analysis["exclusions"]),
        "mad": analysis["mad"],
        "ordenes_de_magnitud": analysis["orders_spanned"],
        "distribucion": [
            {
                "digito": row["digit"],
                "observados": row["observed_count"],
                "esperados": row["expected_count"],
                "observado_porcentaje": row["observed_percent"],
                "esperado_porcentaje": row["theoretical_percent"],
            }
            for row in analysis["distribution"]
        ],
        "advertencias": list(audit.warnings),
        "disclaimer": audit.disclaimer,
    }


def personality_sections(analysis: PersonalityAnalysis):
    """analisis_bigfive conserva sus claves (puntaje o null por rasgo + resumen) para la web;
    la evidencia va en analisis_bigfive_evidencia. Devuelve (bigfive, evidencia, comercial)."""
    profile = analysis.big_five
    bigfive = {LEGACY_TRAIT_KEYS[t.trait]: (t.score.value if t.score else None) for t in profile.traits}
    bigfive["resumen"] = profile.summary
    evidence = {
        "videos_analizados": analysis.analyzed_videos,
        "citas_descartadas": analysis.discarded_quotes,
        "minimo_videos_por_rasgo": MIN_SUPPORTING_VIDEOS,
        "rasgos": {
            LEGACY_TRAIT_KEYS[t.trait]: {
                "puntaje": t.score.value if t.score else None,
                "estado": t.status.value,
                "videos_con_evidencia": t.supporting_videos,
                "cobertura_evidencia": t.evidence_coverage,
                "evidencias": [{"video_id": e.video_id, "cita": e.quote} for e in t.evidence],
            }
            for t in profile.traits
        },
    }
    commercial = {
        "tono_comunicacion": analysis.communication_tone,
        "intereses": list(analysis.interests),
        "afinidad_marcas": list(analysis.brand_affinity),
    }
    return bigfive, evidence, commercial


def legacy_document(creator: Creator, audit: AudienceAudit | None = None,
                    personality: PersonalityAnalysis | None = None):
    """El documento completo de datos_<usuario>.json (lo que escribe save y lo que recibe la web)."""
    data = to_legacy_dict(creator)
    if personality is not None:
        data["analisis_bigfive"], data["analisis_bigfive_evidencia"], data["perfil_comercial"] = \
            personality_sections(personality)
    if audit is not None:
        data["auditoria_audiencia"] = audit_section(audit)
    return data


def _count(value):
    """Solo enteros exactos; los textos del scraper legado ("1.2M") y lo demás quedan como desconocidos."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _video_from_legacy(item):
    video_id = str(item.get("id") or "")
    url = str(item.get("enlace") or "")
    if not video_id.isdigit():
        match = re.search(r"/video/(\d+)", url)
        video_id = match.group(1) if match else ""
    if not video_id or not url.startswith("https://"):
        return None
    description = str(item.get("descripcion") or "").strip()
    try:
        published_at = datetime.fromisoformat(item["fecha_publicacion"]) if item.get("fecha_publicacion") else None
    except (TypeError, ValueError):
        published_at = None
    thumbnail = item.get("miniatura")
    return Video(
        id=video_id, url=url,
        description=description if description and description != SIN_DESCRIPCION else None,
        published_at=published_at,
        thumbnail_url=thumbnail if thumbnail and thumbnail != PLACEHOLDER_VIDEO else None,
        stats=VideoStats(*(_count(item.get(key)) for key in METRIC_KEYS)),
    )


def from_legacy_dict(data, username: Username):
    profile = data.get("perfil") or {}
    videos, seen = [], set()
    for item in data.get("videos_recientes") or []:
        video = _video_from_legacy(item) if isinstance(item, dict) else None
        if video is not None and video.id not in seen:  # se omiten videos sin ID/enlace válidos y repetidos
            seen.add(video.id)
            videos.append(video)
    avatar = profile.get("foto_perfil")
    return Creator(
        username=username,
        profile=PublicProfile(followers=_count(profile.get("seguidores")), following=_count(profile.get("siguiendo")),
                              likes=_count(profile.get("me_gusta")),
                              avatar_url=avatar if avatar and avatar != PLACEHOLDER_FOTO else None),
        videos=tuple(videos),
    )


class LegacyJsonCreatorRepository(CreatorRepository):
    def __init__(self, directory="."):
        self.directory = Path(directory)

    def path_for(self, username: Username):
        return self.directory / f"datos_{username.value}.json"

    def _write(self, path, data):
        """Escritura atómica: un archivo temporal en la misma carpeta y luego os.replace."""
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=4)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        return str(path)

    def save(self, creator: Creator, audit: AudienceAudit | None = None,
             personality: PersonalityAnalysis | None = None):
        """Escribe datos_<usuario>.json completo (reemplaza el anterior) y devuelve su ruta."""
        return self._write(self.path_for(creator.username), legacy_document(creator, audit, personality))

    def load(self, username: Username) -> Creator:
        with open(self.path_for(username), "r", encoding="utf-8") as stream:
            return from_legacy_dict(json.load(stream), username)

    def _update(self, username: Username, sections):
        """Añade o reemplaza las claves indicadas sin tocar el resto del archivo."""
        path = self.path_for(username)
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        data.update(sections)
        return self._write(path, data)

    def save_audit(self, username: Username, audit: AudienceAudit):
        """Añade o reemplaza auditoria_audiencia sin tocar el resto del archivo."""
        return self._update(username, {"auditoria_audiencia": audit_section(audit)})

    def save_personality(self, username: Username, personality: PersonalityAnalysis):
        """Añade o reemplaza analisis_bigfive, analisis_bigfive_evidencia y perfil_comercial."""
        bigfive, evidence, commercial = personality_sections(personality)
        return self._update(username, {"analisis_bigfive": bigfive, "analisis_bigfive_evidencia": evidence,
                                       "perfil_comercial": commercial})
