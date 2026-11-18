// Puntaje de un rasgo Big Five, de 0 a 100. Cada rasgo es independiente (no suman 100).
// null = no hubo evidencia suficiente para puntuarlo; nunca se reemplaza por 0 ni por 50.
export type TraitScore = number | null;

export const TRAIT_SCORE_MIN = 0;
export const TRAIT_SCORE_MAX = 100;

/** Convierte un valor cualquiera en TraitScore; si no es un número dentro de 0-100, devuelve null. */
export function toTraitScore(value: unknown): TraitScore {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  if (value < TRAIT_SCORE_MIN || value > TRAIT_SCORE_MAX) return null;
  return value;
}

export function isScored(score: TraitScore): score is number {
  return score !== null;
}
