"""Caso de uso AuditAudience: Ley de Benford sobre las 5 métricas de todos los videos juntas."""
from truematch.application.ports.creator_repository import CreatorRepository
from truematch.domain.audience_audit.audience_audit import AudienceAudit
from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.username import Username


class AuditAudience:
    def __init__(self, repository: CreatorRepository | None = None):
        self.repository = repository

    @staticmethod
    def audit(creator: Creator) -> AudienceAudit:
        """Vistas, me gusta, comentarios, compartidos y guardados de todos los videos, en una sola muestra."""
        return AudienceAudit.from_values(creator.metric_values())

    def execute(self, username: Username) -> AudienceAudit:
        """Audita un creador ya guardado (sin volver a la fuente) y guarda el resultado."""
        if self.repository is None:
            raise ValueError("AuditAudience.execute necesita un repositorio.")
        audit = self.audit(self.repository.load(username))
        self.repository.save_audit(username, audit)
        return audit
