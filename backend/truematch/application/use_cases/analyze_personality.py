"""Caso de uso AnalyzePersonality: Big Five y perfil comercial de un creador ya guardado (sin volver a la fuente)."""
from truematch.application.ports.creator_repository import CreatorRepository
from truematch.application.ports.personality_analyzer import PersonalityAnalyzer
from truematch.domain.creator_profiling.personality_analysis import PersonalityAnalysis
from truematch.domain.creator_profiling.username import Username


class AnalyzePersonality:
    def __init__(self, repository: CreatorRepository, analyzer: PersonalityAnalyzer):
        self.repository, self.analyzer = repository, analyzer

    def execute(self, username: Username) -> PersonalityAnalysis:
        """Cargar → analizar → guardar. Lanza FileNotFoundError si el creador no está guardado y
        PersonalityAnalysisError si el análisis falla; en ese caso no se modifica lo guardado."""
        personality = self.analyzer.analyze(self.repository.load(username))
        self.repository.save_personality(username, personality)
        return personality
