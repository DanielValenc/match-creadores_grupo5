import type { BigFiveProfile, BigFiveTrait } from './BigFiveProfile';
import { BIG_FIVE_TRAITS } from './BigFiveProfile';

/**
 * Distribución relativa del Big Five: cada rasgo con puntaje como porcentaje entero del total
 * de los rasgos con puntaje. Los porcentajes suman exactamente 100.
 * Los rasgos sin puntaje (evidencia insuficiente) quedan en null y no entran en el reparto.
 */
export type BigFiveDistribution = Readonly<Record<BigFiveTrait, number | null>>;

/**
 * Calcula la distribución relativa con el método del mayor resto: se toma la parte entera de
 * cada porcentaje y los puntos que faltan para llegar a 100 se asignan a los rasgos con mayor
 * parte decimal (en empate, el orden de BIG_FIVE_TRAITS).
 *
 * Devuelve null si ningún rasgo tiene puntaje o si todos los puntajes son 0 (no hay total
 * que repartir).
 */
export function computeBigFiveDistribution(profile: BigFiveProfile): BigFiveDistribution | null {
  const scored = BIG_FIVE_TRAITS.flatMap((trait) => {
    const score = profile.traits[trait].score;
    return score !== null ? [{ trait, score }] : [];
  });
  const total = scored.reduce((sum, s) => sum + s.score, 0);
  if (scored.length === 0 || total <= 0) return null;

  const shares = scored.map(({ trait, score }, order) => {
    const exact = (score / total) * 100;
    const floor = Math.floor(exact);
    return { trait, order, floor, remainder: exact - floor };
  });

  let missing = 100 - shares.reduce((sum, s) => sum + s.floor, 0);
  const byRemainder = [...shares].sort((a, b) => b.remainder - a.remainder || a.order - b.order);
  const result: Record<BigFiveTrait, number | null> = {
    openness: null,
    conscientiousness: null,
    extraversion: null,
    agreeableness: null,
    neuroticism: null,
  };
  for (const s of shares) result[s.trait] = s.floor;
  for (const s of byRemainder) {
    if (missing <= 0) break;
    result[s.trait] = (result[s.trait] as number) + 1;
    missing--;
  }
  return result;
}
