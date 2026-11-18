import type { Creator } from '../../domain/creator-profiling/Creator';
import type { CreatorRepository } from '../../domain/creator-profiling/CreatorRepository';
import type { Username } from '../../domain/creator-profiling/Username';
import { CreatorNotFoundError } from '../../domain/creator-profiling/errors';
import { toCreator } from '../api/creatorMapper';
import fixture from './fixtures/tradingempire.es.json';

export interface MockCreatorRepositoryOptions {
  /** Retraso simulado de analyze(), para ver la pantalla de carga. */
  readonly analyzeDelayMs?: number;
}

// Repositorio sin red, para desarrollar las pantallas sin backend.
// Usa un análisis real guardado; pasa por el mismo mapper que la API.
export class MockCreatorRepository implements CreatorRepository {
  private readonly creator: Creator = toCreator(fixture);
  private readonly analyzeDelayMs: number;

  constructor(options: MockCreatorRepositoryOptions = {}) {
    this.analyzeDelayMs = options.analyzeDelayMs ?? 2_000;
  }

  /** Solo tiene "guardado" al creador del fixture; para otros simula el 404. */
  async getSaved(username: Username): Promise<Creator> {
    if (username !== this.creator.username) throw new CreatorNotFoundError(username);
    return this.creator;
  }

  /** Para cualquier usuario devuelve el análisis del fixture (con su usuario real). */
  async analyze(_username: Username): Promise<Creator> {
    await new Promise((resolve) => setTimeout(resolve, this.analyzeDelayMs));
    return this.creator;
  }
}
