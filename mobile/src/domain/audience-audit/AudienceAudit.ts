// Auditoría de audiencia con la Ley de Benford sobre las métricas de los videos.
// Una desviación no demuestra fraude, y una distribución cercana no demuestra autenticidad:
// el disclaimer debe mostrarse siempre junto al puntaje.

// Se usa si el backend no envía su propio disclaimer: el aviso nunca debe faltar.
export const DEFAULT_AUDIT_DISCLAIMER =
  'Una desviación respecto de Benford no demuestra bots, fraude ni compra de seguidores. ' +
  'Una distribución cercana tampoco demuestra autenticidad.';

/** Valores válidos mínimos para calcular el puntaje orgánico. Con menos, el puntaje es null. */
export const MIN_AUDIT_SAMPLE_SIZE = 110;

export interface BenfordDigit {
  readonly digit: number; // 1-9
  readonly observed: number;
  readonly expected: number;
  readonly observedPercent: number;
  readonly expectedPercent: number;
}

export interface ExcludedRecords {
  readonly missing: number;
  readonly zero: number;
  readonly negative: number;
  readonly invalid: number;
}

export interface AudienceAudit {
  /** 0-100, o null cuando la muestra no permite calcularlo. */
  readonly organicScore: number | null;
  readonly metrics: readonly string[];
  readonly sampleSize: number | null;
  readonly totalRecords: number | null;
  readonly excluded: ExcludedRecords;
  readonly mad: number | null; // desviación absoluta media
  readonly ordersOfMagnitude: number | null;
  readonly distribution: readonly BenfordDigit[];
  readonly warnings: readonly string[];
  readonly disclaimer: string;
}
