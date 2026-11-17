/**
 * Cliente HTTP de TrueMatch Mobile.
 * Consume la API Flask de la rama dev de TrueMatch AI:
 *   GET  /api/health
 *   GET  /api/datos/<usuario>
 *   POST /api/analizar
 */

export interface Perfil {
  foto_perfil?: string | null;
  siguiendo?: number | null;
  seguidores?: number | null;
  me_gusta?: number | null;
}

export interface BigFive {
  Apertura?: number | null;
  Responsabilidad?: number | null;
  Extraversion?: number | null;
  Amabilidad?: number | null;
  Neuroticismo?: number | null;
  resumen?: string;
}

export interface VideoReciente {
  posicion: number;
  enlace: string;
  miniatura?: string | null;
  descripcion?: string | null;
  estado?: string;
  id: string;
  fecha_publicacion?: string | null;
  vistas?: number | null;
  me_gusta?: number | null;
  comentarios?: number | null;
  compartidos?: number | null;
  guardados?: number | null;
}

export interface AfinidadMarca {
  categoria: string;
  motivo: string;
}

export interface PerfilComercial {
  tono_comunicacion?: string;
  intereses?: string[];
  afinidad_marcas?: AfinidadMarca[];
}

export interface DistribucionBenford {
  digito: number;
  observados: number;
  esperados: number;
  observado_porcentaje: number | null;
  esperado_porcentaje: number;
}

export interface AuditoriaAudiencia {
  puntaje_organico: number | null;
  metricas: string[];
  tamano_muestra: number;
  registros_totales: number;
  excluidos: Record<string, number>;
  mad: number | null;
  ordenes_de_magnitud: number;
  distribucion: DistribucionBenford[];
  advertencias: string[];
  disclaimer: string;
}

/** Documento devuelto por legacy_document() en el backend DDD. */
export interface Documento {
  usuario: string;
  perfil: Perfil;
  videos_recientes: VideoReciente[];
  analisis_bigfive?: BigFive;
  analisis_bigfive_evidencia?: Record<string, unknown>;
  perfil_comercial?: PerfilComercial;
  auditoria_audiencia?: AuditoriaAudiencia;
}

interface ApiEnvelope<T> {
  ok: boolean;
  error?: string;
  datos?: T;
  servicio?: string;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Configura esta variable en mobile/.env. No uses localhost desde un teléfono físico.
export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? "")
  .trim()
  .replace(/\/+$/, "");

export const USAR_GUARDADO = process.env.EXPO_PUBLIC_USAR_GUARDADO === "1";
export const TIMEOUT_ANALISIS_MS = 600_000;
export const TIMEOUT_RAPIDO_MS = 8_000;

function getBaseUrl(): string {
  if (!API_URL) {
    throw new Error(
      "Falta EXPO_PUBLIC_API_URL. Configúrala en mobile/.env y reinicia Expo con npx expo start -c.",
    );
  }
  return API_URL;
}

async function requestEnvelope<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = TIMEOUT_RAPIDO_MS,
  externalSignal?: AbortSignal,
): Promise<ApiEnvelope<T>> {
  const controller = new AbortController();
  const relayAbort = () => controller.abort();

  if (externalSignal?.aborted) {
    controller.abort();
  } else {
    externalSignal?.addEventListener("abort", relayAbort, { once: true });
  }

  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    let response: Response;

    try {
      response = await fetch(`${getBaseUrl()}${path}`, {
        ...options,
        signal: controller.signal,
      });
    } catch (error) {
      if (externalSignal?.aborted) {
        throw new Error("El análisis fue cancelado.");
      }
      if (controller.signal.aborted) {
        throw new Error(
          `La solicitud superó el tiempo límite de ${Math.round(timeoutMs / 1000)} segundos.`,
        );
      }
      const detail = error instanceof Error ? error.message : String(error);
      throw new Error(
        `No se pudo conectar con Flask: ${detail}. Comprueba la IP, el puerto 5000, el Wi-Fi y el Firewall de Windows.`,
      );
    }

    let payload: ApiEnvelope<T>;
    try {
      payload = (await response.json()) as ApiEnvelope<T>;
    } catch {
      throw new ApiError(
        "Flask devolvió una respuesta que no es JSON válido.",
        response.status,
      );
    }

    if (!response.ok || payload.ok !== true) {
      throw new ApiError(
        payload.error ||
          `Error HTTP ${response.status} al consultar el backend.`,
        response.status,
      );
    }

    return payload;
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", relayAbort);
  }
}

export async function getHealth(): Promise<boolean> {
  const result = await requestEnvelope<unknown>(
    "/api/health",
    { method: "GET" },
    TIMEOUT_RAPIDO_MS,
  );
  return result.ok === true;
}

export async function getAnalisisGuardado(
  username: string,
): Promise<Documento> {
  const cleanUsername = username.trim().replace(/^@/, "");
  const result = await requestEnvelope<Documento>(
    `/api/datos/${encodeURIComponent(cleanUsername)}`,
    { method: "GET" },
    TIMEOUT_RAPIDO_MS,
  );

  if (!result.datos) {
    throw new ApiError("El backend no devolvió el análisis guardado.", 502);
  }

  return result.datos;
}

export async function analizarCreador(
  username: string,
  signal?: AbortSignal,
): Promise<Documento> {
  const cleanUsername = username.trim().replace(/^@/, "");

  if (!cleanUsername) {
    throw new Error("Ingresa un usuario de TikTok.");
  }

  // Modo opcional para probar usando un análisis que ya exista en el backend.
  if (USAR_GUARDADO) {
    try {
      return await getAnalisisGuardado(cleanUsername);
    } catch (error) {
      // Solo se inicia un análisis nuevo cuando el archivo guardado no existe.
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
    }
  }

  const result = await requestEnvelope<Documento>(
    "/api/analizar",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: cleanUsername }),
    },
    TIMEOUT_ANALISIS_MS,
    signal,
  );

  if (!result.datos) {
    throw new ApiError(
      "El backend terminó sin devolver el documento del creador.",
      502,
    );
  }

  return result.datos;
}
