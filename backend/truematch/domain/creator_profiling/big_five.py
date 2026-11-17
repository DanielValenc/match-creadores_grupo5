"""BigFiveProfile y TraitScore (README §6.4 y §6.6, con la conciliación de docs/plan-backend.md §4).

Los cinco rasgos son independientes: no se normalizan ni tienen que sumar 100. Un rasgo solo conserva su
puntaje si tiene citas literales verificadas de al menos MIN_SUPPORTING_VIDEOS videos distintos.
"""
from dataclasses import dataclass
from enum import Enum
import math

from .trait_evidence import TraitEvidence

MIN_SUPPORTING_VIDEOS = 2


class Trait(Enum):
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"

    @property
    def label(self):
        return {"openness": "Apertura", "conscientiousness": "Responsabilidad", "extraversion": "Extraversión",
                "agreeableness": "Amabilidad", "neuroticism": "Neuroticismo"}[self.value]


class TraitStatus(Enum):
    SCORED = "scored"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_SCORE = "invalid_score"  # hay evidencia suficiente, pero la IA no dio un número usable


@dataclass(frozen=True)
class TraitScore:
    value: int

    def __post_init__(self):
        if isinstance(self.value, bool) or not isinstance(self.value, int) or not 0 <= self.value <= 100:
            raise ValueError("TraitScore debe ser un entero entre 0 y 100.")

    @classmethod
    def from_raw(cls, raw):
        """Redondea y recorta a 0-100 un número de la IA; rechaza lo que no sea un número finito."""
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            raise ValueError("El puntaje no es un número.")
        return cls(round(min(100.0, max(0.0, float(raw)))))


@dataclass(frozen=True)
class TraitAssessment:
    trait: Trait
    score: TraitScore | None
    status: TraitStatus
    evidence: tuple[TraitEvidence, ...]
    evidence_coverage: int  # 100 × videos con evidencia / videos analizados; no reemplaza al puntaje

    def __post_init__(self):
        if (self.status is TraitStatus.SCORED) != (self.score is not None):
            raise ValueError("Solo un rasgo con estado 'scored' tiene puntaje.")

    @property
    def supporting_videos(self):
        return len({item.video_id for item in self.evidence})

    @classmethod
    def assess(cls, trait, raw_score, evidence, analyzed_videos):
        """Aplica la regla del dominio a un puntaje propuesto y a evidencia ya verificada."""
        evidence = tuple(evidence)
        supporting = len({item.video_id for item in evidence})
        coverage = round(100 * supporting / analyzed_videos) if analyzed_videos else 0
        if supporting < MIN_SUPPORTING_VIDEOS:
            return cls(trait, None, TraitStatus.INSUFFICIENT_EVIDENCE, evidence, coverage)
        try:
            score = TraitScore.from_raw(raw_score)
        except ValueError:
            return cls(trait, None, TraitStatus.INVALID_SCORE, evidence, coverage)
        return cls(trait, score, TraitStatus.SCORED, evidence, coverage)


@dataclass(frozen=True)
class BigFiveProfile:
    traits: tuple[TraitAssessment, ...]
    summary: str = ""

    def __post_init__(self):
        traits = tuple(self.traits)
        if sorted(t.trait.value for t in traits) != sorted(t.value for t in Trait):
            raise ValueError("El perfil Big Five necesita los cinco rasgos exactamente una vez.")
        order = list(Trait)
        object.__setattr__(self, "traits", tuple(sorted(traits, key=lambda t: order.index(t.trait))))

    def get(self, trait):
        return next(t for t in self.traits if t.trait is trait)
