"""Video: publicación reciente del creador, con sus métricas públicas."""
from dataclasses import dataclass, field
from datetime import datetime

from .counts import optional_count

METRIC_NAMES = ("views", "likes", "comments", "shares", "saves")


@dataclass(frozen=True)
class VideoStats:
    """Métricas de un video. None significa «no disponible», nunca cero."""
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None

    def __post_init__(self):
        for name in METRIC_NAMES:
            optional_count(name, getattr(self, name))

    def values(self):
        """Las cinco métricas en el orden de METRIC_NAMES, incluidas las None."""
        return tuple(getattr(self, name) for name in METRIC_NAMES)


@dataclass(frozen=True)
class Video:
    id: str
    url: str
    description: str | None = None
    published_at: datetime | None = None
    thumbnail_url: str | None = None
    stats: VideoStats = field(default_factory=VideoStats)

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.isdigit():
            raise ValueError("El ID del video debe ser un texto numérico.")
        if not isinstance(self.url, str) or not self.url.startswith("https://"):
            raise ValueError("La URL del video debe empezar con https://.")
        if not isinstance(self.stats, VideoStats):
            raise ValueError("stats debe ser un VideoStats.")

    def has_description(self):
        return bool(self.description and self.description.strip())
