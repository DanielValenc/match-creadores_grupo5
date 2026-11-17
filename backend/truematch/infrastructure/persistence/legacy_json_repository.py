"""Repositorio JSON en el formato heredado datos_<usuario>.json.

Mantiene las claves que leen analisis_bigfive.py y la web (usuario, perfil.*, videos_recientes[].*) y añade,
por video, id, fecha_publicacion y las cinco métricas. Los contadores son enteros exactos o null (desconocido),
nunca textos abreviados como "1.2M".
"""
import json
import os
from pathlib import Path
import tempfile

from truematch.domain.creator_profiling.creator import Creator

PLACEHOLDER_FOTO = "https://via.placeholder.com/150?text=Sin+Foto"
PLACEHOLDER_VIDEO = "https://via.placeholder.com/300x400?text=Video"
SIN_DESCRIPCION = "Sin descripción disponible"


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
                "vistas": video.stats.views,
                "me_gusta": video.stats.likes,
                "comentarios": video.stats.comments,
                "compartidos": video.stats.shares,
                "guardados": video.stats.saves,
            }
            for position, video in enumerate(creator.videos, start=1)
        ],
    }


class LegacyJsonCreatorRepository:
    def __init__(self, directory="."):
        self.directory = Path(directory)

    def path_for(self, username):
        return self.directory / f"datos_{username.value}.json"

    def save(self, creator: Creator):
        """Escribe datos_<usuario>.json de forma atómica y devuelve su ruta."""
        path = self.path_for(creator.username)
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(to_legacy_dict(creator), stream, ensure_ascii=False, indent=4)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        return path
