"""Caso de uso AnalyzeCreator: fuente → auditoría de audiencia → personalidad → repositorio."""
from dataclasses import dataclass

from truematch.application.ports.creator_repository import CreatorRepository
from truematch.application.ports.creator_source import CreatorSource
from truematch.application.ports.personality_analyzer import PersonalityAnalysisError, PersonalityAnalyzer
from truematch.domain.audience_audit.audience_audit import AudienceAudit
from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.personality_analysis import PersonalityAnalysis
from truematch.domain.creator_profiling.username import Username

from .audit_audience import AuditAudience


@dataclass(frozen=True)
class AnalysisResult:
    creator: Creator
    location: str
    audit: AudienceAudit
    personality: PersonalityAnalysis | None   # None si no se pidió o si falló
    personality_error: str | None = None


class AnalyzeCreator:
    def __init__(self, source: CreatorSource, repository: CreatorRepository,
                 analyzer: PersonalityAnalyzer | None = None):
        self.source, self.repository, self.analyzer = source, repository, analyzer

    def execute(self, username: Username) -> AnalysisResult:
        """Si la fuente falla, lanza su excepción y no guarda nada. Si solo falla el análisis de personalidad,
        se guardan igual el creador y la auditoría, y el error queda en personality_error."""
        creator = self.source.fetch(username)
        audit = AuditAudience.audit(creator)
        personality, error = None, None
        if self.analyzer is not None:
            try:
                personality = self.analyzer.analyze(creator)
            except PersonalityAnalysisError as failure:
                error = str(failure)
        location = self.repository.save(creator, audit=audit, personality=personality)
        return AnalysisResult(creator, location, audit, personality, error)
