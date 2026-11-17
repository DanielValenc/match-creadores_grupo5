"""Puerto PersonalityAnalyzer: estima el Big Five y el perfil comercial a partir de los videos del creador."""
from abc import ABC, abstractmethod

from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.personality_analysis import PersonalityAnalysis


class PersonalityAnalysisError(RuntimeError):
    """El análisis no se pudo completar (proveedor caído, respuesta inválida o sin descripciones)."""


class PersonalityAnalyzer(ABC):
    @abstractmethod
    def analyze(self, creator: Creator) -> PersonalityAnalysis:
        """Lanza PersonalityAnalysisError si no se puede analizar."""
