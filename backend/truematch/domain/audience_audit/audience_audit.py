"""AudienceAudit: revisión de las métricas del creador con la Ley de Benford."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .benford import DISCLAIMER, analyze_values
from .organic_score import MIN_ORDERS_SPANNED, MIN_VALID_VALUES, OrganicScore


@dataclass(frozen=True)
class AudienceAudit:
    analysis: Mapping            # resultado completo de benford.analyze_values (solo lectura)
    organic_score: OrganicScore | None
    warnings: tuple[str, ...]
    disclaimer: str = DISCLAIMER

    @classmethod
    def from_values(cls, values):
        """Audita los valores recibidos. No sabe de dónde salieron (README §6.3)."""
        analysis = analyze_values(list(values))
        enough_values = analysis["valid_records"] >= MIN_VALID_VALUES
        enough_range = (analysis["orders_spanned"] is not None
                        and analysis["orders_spanned"] >= MIN_ORDERS_SPANNED)
        score = OrganicScore.from_mad(analysis["mad"], analysis["valid_records"]) if enough_values and enough_range else None
        return cls(
            analysis=MappingProxyType(analysis),
            organic_score=score,
            warnings=tuple(analysis["warnings"]),
            disclaimer=analysis["disclaimer"],
        )

    @property
    def score_available(self):
        return self.organic_score is not None
