"""Puerto CreatorRepository: dónde se guardan y se leen los creadores analizados."""
from abc import ABC, abstractmethod

from truematch.domain.audience_audit.audience_audit import AudienceAudit
from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.personality_analysis import PersonalityAnalysis
from truematch.domain.creator_profiling.username import Username


class CreatorRepository(ABC):
    @abstractmethod
    def save(self, creator: Creator, audit: AudienceAudit | None = None,
             personality: PersonalityAnalysis | None = None) -> str:
        """Guarda el creador con sus resultados (reemplaza lo anterior) y devuelve dónde quedó."""

    @abstractmethod
    def load(self, username: Username) -> Creator:
        """Lee un creador guardado. Lanza FileNotFoundError si no existe."""

    @abstractmethod
    def save_audit(self, username: Username, audit: AudienceAudit) -> str:
        """Añade o reemplaza solo la auditoría de un creador ya guardado y devuelve dónde quedó."""

    @abstractmethod
    def save_personality(self, username: Username, personality: PersonalityAnalysis) -> str:
        """Añade o reemplaza solo el análisis de personalidad de un creador ya guardado y devuelve dónde quedó."""
