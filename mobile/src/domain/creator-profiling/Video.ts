// Video reciente del creador con sus métricas públicas.
// Las métricas son null cuando no se pudieron extraer.
export interface Video {
  readonly id: string;
  readonly position: number;
  readonly url: string;
  readonly thumbnailUrl: string | null;
  readonly description: string;
  readonly publishedAt: string | null; // ISO 8601
  readonly extractionStatus: string;
  readonly views: number | null;
  readonly likes: number | null;
  readonly comments: number | null;
  readonly shares: number | null;
  readonly saves: number | null;
}
