import type { AudienceAudit, BenfordDigit } from '../../domain/audience-audit/AudienceAudit';
import { DEFAULT_AUDIT_DISCLAIMER } from '../../domain/audience-audit/AudienceAudit';
import type { SectorAffinity } from '../../domain/brand-matching/SectorAffinity';
import type {
  BigFiveProfile,
  BigFiveTrait,
  TraitAssessment,
  TraitEvidence,
} from '../../domain/creator-profiling/BigFiveProfile';
import { BIG_FIVE_TRAITS } from '../../domain/creator-profiling/BigFiveProfile';
import type { Creator } from '../../domain/creator-profiling/Creator';
import type { PublicProfile } from '../../domain/creator-profiling/PublicProfile';
import { toTraitScore } from '../../domain/creator-profiling/TraitScore';
import type { Username } from '../../domain/creator-profiling/Username';
import { parseUsername } from '../../domain/creator-profiling/Username';
import type { Video } from '../../domain/creator-profiling/Video';
import { AnalysisServiceError } from '../../domain/creator-profiling/errors';

// Traduce el documento JSON del backend (README §12, claves en español) al modelo del dominio.
// Regla: un dato ausente o inválido es null, nunca 0. null significa "no se sabe".

type Json = Record<string, unknown>;

const TRAIT_KEYS: Record<BigFiveTrait, string> = {
  openness: 'Apertura',
  conscientiousness: 'Responsabilidad',
  extraversion: 'Extraversion',
  agreeableness: 'Amabilidad',
  neuroticism: 'Neuroticismo',
};

function isObject(value: unknown): value is Json {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function obj(value: unknown): Json {
  return isObject(value) ? value : {};
}

function arr(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function num(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function str(value: unknown): string | null {
  return typeof value === 'string' && value.trim() !== '' ? value : null;
}

function strings(value: unknown): string[] {
  return arr(value).filter((v): v is string => typeof v === 'string' && v.trim() !== '');
}

function mapProfile(raw: unknown): PublicProfile {
  const p = obj(raw);
  return {
    avatarUrl: str(p.foto_perfil),
    following: num(p.siguiendo),
    followers: num(p.seguidores),
    likes: num(p.me_gusta),
  };
}

function mapVideo(raw: unknown, index: number): Video | null {
  const v = obj(raw);
  const id = str(v.id);
  if (id === null) return null;
  return {
    id,
    position: num(v.posicion) ?? index + 1,
    url: str(v.enlace) ?? '',
    thumbnailUrl: str(v.miniatura),
    description: typeof v.descripcion === 'string' ? v.descripcion : '',
    publishedAt: str(v.fecha_publicacion),
    extractionStatus: str(v.estado) ?? '',
    views: num(v.vistas),
    likes: num(v.me_gusta),
    comments: num(v.comentarios),
    shares: num(v.compartidos),
    saves: num(v.guardados),
  };
}

function mapEvidence(raw: unknown): TraitEvidence | null {
  const e = obj(raw);
  const videoId = str(e.video_id);
  const quote = str(e.cita);
  return videoId !== null && quote !== null ? { videoId, quote } : null;
}

function mapTrait(scores: Json, details: Json, key: string): TraitAssessment {
  const detail = isObject(details[key]) ? details[key] : null;
  // El detalle con evidencias es la fuente principal; el resumen plano es el respaldo.
  const score = toTraitScore(detail ? detail.puntaje : scores[key]);
  return {
    score,
    status: score === null ? 'insufficient_evidence' : 'scored',
    videosWithEvidence: num(detail?.videos_con_evidencia) ?? 0,
    evidenceCoverage: num(detail?.cobertura_evidencia) ?? 0,
    evidence: arr(detail?.evidencias)
      .map(mapEvidence)
      .filter((e): e is TraitEvidence => e !== null),
  };
}

function mapBigFive(rawScores: unknown, rawEvidence: unknown): BigFiveProfile {
  const scores = obj(rawScores);
  const evidence = obj(rawEvidence);
  const details = obj(evidence.rasgos);
  const traits = Object.fromEntries(
    BIG_FIVE_TRAITS.map((t) => [t, mapTrait(scores, details, TRAIT_KEYS[t])]),
  ) as Record<BigFiveTrait, TraitAssessment>;
  return {
    traits,
    summary: str(scores.resumen),
    videosAnalyzed: num(evidence.videos_analizados),
    minVideosPerTrait: num(evidence.minimo_videos_por_rasgo),
  };
}

function mapSectorAffinity(raw: unknown): SectorAffinity | null {
  const a = obj(raw);
  const category = str(a.categoria);
  return category === null ? null : { category, reason: str(a.motivo) ?? '' };
}

function mapDigit(raw: unknown): BenfordDigit | null {
  const d = obj(raw);
  const digit = num(d.digito);
  if (digit === null) return null;
  return {
    digit,
    observed: num(d.observados) ?? 0,
    expected: num(d.esperados) ?? 0,
    observedPercent: num(d.observado_porcentaje) ?? 0,
    expectedPercent: num(d.esperado_porcentaje) ?? 0,
  };
}

function mapAudit(raw: unknown): AudienceAudit | null {
  if (!isObject(raw)) return null;
  const excluded = obj(raw.excluidos);
  return {
    organicScore: num(raw.puntaje_organico),
    metrics: strings(raw.metricas),
    sampleSize: num(raw.tamano_muestra),
    totalRecords: num(raw.registros_totales),
    excluded: {
      missing: num(excluded.missing) ?? 0,
      zero: num(excluded.zero) ?? 0,
      negative: num(excluded.negative) ?? 0,
      invalid: num(excluded.invalid) ?? 0,
    },
    mad: num(raw.mad),
    ordersOfMagnitude: num(raw.ordenes_de_magnitud),
    distribution: arr(raw.distribucion)
      .map(mapDigit)
      .filter((d): d is BenfordDigit => d !== null),
    warnings: strings(raw.advertencias),
    disclaimer: str(raw.disclaimer) ?? DEFAULT_AUDIT_DISCLAIMER,
  };
}

/**
 * Convierte la respuesta del backend en un Creator.
 * Lanza AnalysisServiceError si el documento no es reconocible.
 */
export function toCreator(raw: unknown, requested?: Username): Creator {
  if (!isObject(raw)) {
    throw new AnalysisServiceError('El servicio devolvió una respuesta con formato inválido.');
  }
  const username = parseUsername(str(raw.usuario) ?? '') ?? requested;
  if (!username) {
    throw new AnalysisServiceError('La respuesta del servicio no incluye un usuario válido.');
  }
  const commercial = obj(raw.perfil_comercial);
  return {
    username,
    profile: mapProfile(raw.perfil),
    videos: arr(raw.videos_recientes)
      .map(mapVideo)
      .filter((v): v is Video => v !== null),
    bigFive: mapBigFive(raw.analisis_bigfive, raw.analisis_bigfive_evidencia),
    communicationTone: str(commercial.tono_comunicacion),
    interests: strings(commercial.intereses),
    sectorAffinities: arr(commercial.afinidad_marcas)
      .map(mapSectorAffinity)
      .filter((a): a is SectorAffinity => a !== null),
    audit: mapAudit(raw.auditoria_audiencia),
  };
}
