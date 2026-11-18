import type { Creator } from './Creator';
import type { Username } from './Username';

// Puerto: la infraestructura lo implementa (API real o mock).
// Ambos métodos lanzan solo errores del dominio (ver errors.ts).
export interface CreatorRepository {
  /** Devuelve el último análisis guardado. Lanza CreatorNotFoundError si no hay uno. */
  getSaved(username: Username): Promise<Creator>;

  /** Ejecuta un análisis nuevo y lo devuelve. Puede tardar varios minutos. */
  analyze(username: Username): Promise<Creator>;
}
