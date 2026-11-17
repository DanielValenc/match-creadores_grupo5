"""Creator: raíz del agregado de Creator Profiling."""
from dataclasses import dataclass, field

from .public_profile import PublicProfile
from .username import Username
from .video import Video


@dataclass(frozen=True)
class Creator:
    username: Username
    profile: PublicProfile = field(default_factory=PublicProfile)
    videos: tuple[Video, ...] = ()

    def __post_init__(self):
        if not isinstance(self.username, Username):
            raise ValueError("username debe ser un Username.")
        if not isinstance(self.profile, PublicProfile):
            raise ValueError("profile debe ser un PublicProfile.")
        videos = tuple(self.videos)
        if not all(isinstance(video, Video) for video in videos):
            raise ValueError("videos debe contener solo objetos Video.")
        ids = [video.id for video in videos]
        if len(ids) != len(set(ids)):
            raise ValueError("Un creador no puede tener dos videos con el mismo ID.")
        object.__setattr__(self, "videos", videos)

    def descriptions(self):
        """Descripciones no vacías de los videos, en su orden."""
        return [video.description.strip() for video in self.videos if video.has_description()]

    def metric_values(self):
        """Las cinco métricas de todos los videos juntas (decisión del plan para Benford), incluidas las None."""
        return [value for video in self.videos for value in video.stats.values()]
