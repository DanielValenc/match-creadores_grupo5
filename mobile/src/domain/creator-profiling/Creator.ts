import type { AudienceAudit } from '../audience-audit/AudienceAudit';
import type { SectorAffinity } from '../brand-matching/SectorAffinity';
import type { BigFiveProfile } from './BigFiveProfile';
import type { PublicProfile } from './PublicProfile';
import type { Username } from './Username';
import type { Video } from './Video';

// Agregado raíz: el resultado completo del análisis de un creador.
export interface Creator {
  readonly username: Username;
  readonly profile: PublicProfile;
  readonly videos: readonly Video[];
  readonly bigFive: BigFiveProfile;
  readonly communicationTone: string | null;
  readonly interests: readonly string[];
  readonly sectorAffinities: readonly SectorAffinity[];
  /** null si el análisis no incluye auditoría. */
  readonly audit: AudienceAudit | null;
}
