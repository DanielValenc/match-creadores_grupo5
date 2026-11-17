"""PersonalityAnalysis: resultado del análisis de personalidad y perfil comercial de un creador."""
from dataclasses import dataclass

from .big_five import BigFiveProfile


@dataclass(frozen=True)
class PersonalityAnalysis:
    big_five: BigFiveProfile
    communication_tone: str
    interests: tuple[str, ...]
    brand_affinity: tuple[dict, ...]   # [{"categoria", "motivo"}]; pasará a SectorAffinity en Brand Matching
    analyzed_videos: int               # videos enviados al analizador
    discarded_quotes: int              # citas que no aparecen literalmente o citan un video desconocido
