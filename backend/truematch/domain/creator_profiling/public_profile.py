"""PublicProfile: lo visible de la cuenta (seguidores, siguiendo y me gusta)."""
from dataclasses import dataclass

from .counts import optional_count


@dataclass(frozen=True)
class PublicProfile:
    followers: int | None = None
    following: int | None = None
    likes: int | None = None
    video_count: int | None = None
    nickname: str | None = None
    avatar_url: str | None = None

    def __post_init__(self):
        for name in ("followers", "following", "likes", "video_count"):
            optional_count(name, getattr(self, name))
