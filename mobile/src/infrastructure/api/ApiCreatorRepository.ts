import type { Creator } from '../../domain/creator-profiling/Creator';
import type { CreatorRepository } from '../../domain/creator-profiling/CreatorRepository';
import type { Username } from '../../domain/creator-profiling/Username';
import {
  AnalysisServiceError,
  CreatorBusyError,
  CreatorNotFoundError,
} from '../../domain/creator-profiling/errors';
import { toCreator } from './creatorMapper';

// Leer un resultado guardado es rápido; un análisis abre TikTok y llama a la IA.
const SAVED_TIMEOUT_MS = 15_000;
const ANALYZE_TIMEOUT_MS = 5 * 60_000;

export interface ApiCreatorRepositoryOptions {
  readonly savedTimeoutMs?: number;
  readonly analyzeTimeoutMs?: number;
  readonly fetchFn?: typeof fetch;
}

// Implementa el puerto con la API de la web (README §13.2).
// Solo deja salir errores del dominio.
export class ApiCreatorRepository implements CreatorRepository {
  private readonly baseUrl: string;
  private readonly savedTimeoutMs: number;
  private readonly analyzeTimeoutMs: number;
  private readonly fetchFn: typeof fetch;

  constructor(baseUrl: string, options: ApiCreatorRepositoryOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.savedTimeoutMs = options.savedTimeoutMs ?? SAVED_TIMEOUT_MS;
    this.analyzeTimeoutMs = options.analyzeTimeoutMs ?? ANALYZE_TIMEOUT_MS;
    this.fetchFn = options.fetchFn ?? fetch;
  }

  getSaved(username: Username): Promise<Creator> {
    return this.request(
      username,
      `/api/datos/${encodeURIComponent(username)}`,
      { method: 'GET' },
      this.savedTimeoutMs,
    );
  }

  analyze(username: Username): Promise<Creator> {
    return this.request(
      username,
      '/api/analizar',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
      },
      this.analyzeTimeoutMs,
    );
  }

  private async request(
    username: Username,
    path: string,
    init: RequestInit,
    timeoutMs: number,
  ): Promise<Creator> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let response: Response;
    let body: unknown;
    try {
      response = await this.fetchFn(`${this.baseUrl}${path}`, {
        ...init,
        headers: { Accept: 'application/json', ...init.headers },
        signal: controller.signal,
      });
      body = await response.json().catch(() => null);
    } catch (error) {
      const timedOut = controller.signal.aborted;
      throw new AnalysisServiceError(
        timedOut
          ? 'El servicio de análisis tardó demasiado en responder.'
          : 'No se pudo conectar con el servicio de análisis.',
        { cause: error },
      );
    } finally {
      clearTimeout(timer);
    }

    if (response.ok) return toCreator(body, username);
    throw this.toDomainError(response.status, body, username);
  }

  private toDomainError(status: number, body: unknown, username: Username): Error {
    switch (status) {
      case 404:
        return new CreatorNotFoundError(username);
      case 409:
        return new CreatorBusyError(username);
      case 502:
        return new AnalysisServiceError(
          serverMessage(body) ?? 'TikTok o el proveedor de IA no respondieron correctamente.',
        );
      default:
        // 400, 500, 503 y cualquier otro: fallo del servicio, con el mensaje del backend si lo hay.
        return new AnalysisServiceError(
          serverMessage(body) ?? `El servicio de análisis respondió con error ${status}.`,
        );
    }
  }
}

function serverMessage(body: unknown): string | null {
  if (typeof body !== 'object' || body === null) return null;
  const { error } = body as { error?: unknown };
  return typeof error === 'string' && error.trim() !== '' ? error : null;
}
