import type { TraitScore } from './TraitScore';

export const BIG_FIVE_TRAITS = [
  'openness',
  'conscientiousness',
  'extraversion',
  'agreeableness',
  'neuroticism',
] as const;

export type BigFiveTrait = (typeof BIG_FIVE_TRAITS)[number];

// Cita textual de un video que respalda el puntaje de un rasgo.
export interface TraitEvidence {
  readonly videoId: string;
  readonly quote: string;
}

export type TraitStatus = 'scored' | 'insufficient_evidence';

export interface TraitAssessment {
  readonly score: TraitScore;
  readonly status: TraitStatus;
  readonly videosWithEvidence: number;
  readonly evidenceCoverage: number; // porcentaje 0-100 de videos con evidencia
  readonly evidence: readonly TraitEvidence[];
}

export interface BigFiveProfile {
  readonly traits: Readonly<Record<BigFiveTrait, TraitAssessment>>;
  readonly summary: string | null;
  readonly videosAnalyzed: number | null;
  readonly minVideosPerTrait: number | null;
}

/** true si al menos un rasgo tiene puntaje. */
export function hasAnyScore(profile: BigFiveProfile): boolean {
  return BIG_FIVE_TRAITS.some((t) => profile.traits[t].score !== null);
}
