// Errores del dominio. La presentación decide el mensaje según `kind`,
// sin conocer códigos HTTP ni detalles de la infraestructura.

export type CreatorErrorKind = 'not_found' | 'busy' | 'service_failure';

export abstract class CreatorError extends Error {
  abstract readonly kind: CreatorErrorKind;
}

/** El creador no existe, o no hay análisis guardado para él. */
export class CreatorNotFoundError extends CreatorError {
  readonly kind = 'not_found' as const;
  constructor(readonly username: string) {
    super(`No se encontró el creador "${username}".`);
    this.name = 'CreatorNotFoundError';
  }
}

/** Ya hay un análisis en curso para este creador. */
export class CreatorBusyError extends CreatorError {
  readonly kind = 'busy' as const;
  constructor(readonly username: string) {
    super(`Ya se está analizando a "${username}". Inténtalo en unos minutos.`);
    this.name = 'CreatorBusyError';
  }
}

/** El servicio de análisis falló, no respondió a tiempo o devolvió datos inválidos. */
export class AnalysisServiceError extends CreatorError {
  readonly kind = 'service_failure' as const;
  constructor(message = 'El servicio de análisis no está disponible.', options?: { cause?: unknown }) {
    super(message, options);
    this.name = 'AnalysisServiceError';
  }
}

export function isCreatorError(error: unknown): error is CreatorError {
  return error instanceof CreatorError;
}
