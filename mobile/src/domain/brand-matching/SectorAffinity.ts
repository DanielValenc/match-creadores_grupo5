// Sector comercial afín al creador, con el motivo en lenguaje natural.
// No lleva puntaje a propósito: el modelo no produce una cifra fiable de afinidad.
export interface SectorAffinity {
  readonly category: string;
  readonly reason: string;
}
