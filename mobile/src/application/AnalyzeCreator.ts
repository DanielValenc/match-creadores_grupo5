import type { Creator } from '../domain/creator-profiling/Creator';
import type { CreatorRepository } from '../domain/creator-profiling/CreatorRepository';
import type { Username } from '../domain/creator-profiling/Username';
import { CreatorNotFoundError } from '../domain/creator-profiling/errors';

export interface AnalyzeCreatorOptions {
  /** Ignora el resultado guardado y fuerza un análisis nuevo. */
  readonly refresh?: boolean;
}

// Caso de uso: obtener el análisis de un creador.
// Primero intenta leer el resultado guardado (rápido); si no existe, lanza el análisis.
export class AnalyzeCreator {
  constructor(private readonly repository: CreatorRepository) {}

  async execute(username: Username, options: AnalyzeCreatorOptions = {}): Promise<Creator> {
    if (!options.refresh) {
      try {
        return await this.repository.getSaved(username);
      } catch (error) {
        if (!(error instanceof CreatorNotFoundError)) throw error;
      }
    }
    return this.repository.analyze(username);
  }
}
