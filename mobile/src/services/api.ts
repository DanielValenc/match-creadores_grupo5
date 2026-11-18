import {
  API_URL,
  TIMEOUT_ANALISIS_MS,
  TIMEOUT_RAPIDO_MS,
  USAR_GUARDADO,
} from "../config";

export type BigFive = {
  Apertura: number | null;
  Responsabilidad: number | null;
  Extraversion: number | null;
  Amabilidad: number | null;
  Neuroticismo: number | null;
  resumen?: string;
};

export type Video = {
  posicion: number;
  enlace: string;
  miniatura: string;
  descripcion: string;
  vistas?: number | null;
  me_gusta?: number | null;
  comentarios?: number | null;
  compartidos?: number | null;
  guardados?: number | null;
};

export type Perfil = {
  foto_perfil?: string | null;
  siguiendo?: number | null;
  seguidores?: number | null;
  me_gusta?: number | null;
};

export type AfinidadMarca = {
  categoria: string;
  motivo: string;
};

export type PerfilComercial = {
  tono_comunicacion?: string;
  intereses?: string[];
  afinidad_marcas?: AfinidadMarca[];
};

export type DistribucionBenford = {
  digito: number;
  observados?: number;
  esperados?: number;
  observado_porcentaje: number | null;
  esperado_porcentaje: number;
};

export type AuditoriaAudiencia = {
  puntaje_organico: number | null;
  tamano_muestra: number;
  registros_totales?: number;
  metricas?: string[];
  excluidos?: Record<string, number>;
  mad?: number | null;
  ordenes_de_magnitud?: number;
  distribucion?: DistribucionBenford[];
  advertencias: string[];
  disclaimer: string;
};

export type Documento = {
  usuario: string;
  perfil: Perfil;
  videos_recientes: Video[];
  analisis_bigfive?: BigFive;
  analisis_bigfive_evidencia?: Record<string, unknown>;
  perfil_comercial?: PerfilComercial;
  auditoria_audiencia?: AuditoriaAudiencia;
};

export type CreadorResumen = {
  usuario: string;
  foto_perfil: string | null;
  seguidores: number | null;
  puntaje_organico: number | null;
  actualizado: string;
};

export type PropuestaNueva = {
  usuario_creador: string;
  marca: string;
  correo_contacto: string;
  sector: string;
  campana: string;
  mensaje: string;
  presupuesto?: number | null;
};

export type Propuesta = PropuestaNueva & {
  id: string;
  estado: string;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function pedir<T>(
  ruta: string,
  init: RequestInit = {},
  timeoutMs = TIMEOUT_RAPIDO_MS,
): Promise<T> {
  const controlador = new AbortController();
  const timer = setTimeout(() => controlador.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_URL}${ruta}`, {
      ...init,
      signal: controlador.signal,
    });

    let cuerpo: any = null;

    try {
      cuerpo = await response.json();
    } catch {
      // La respuesta no contenía JSON.
    }

    if (!response.ok || cuerpo?.ok !== true) {
      throw new ApiError(
        cuerpo?.error ??
          `El servidor respondió con el código ${response.status}.`,
      );
    }

    return cuerpo as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error?.name === "AbortError") {
      throw new ApiError(
        `El servidor (${API_URL}) tardó demasiado en responder.`,
      );
    }

    throw new ApiError(
      `No se pudo conectar con el servidor (${API_URL}). Comprueba que Flask esté encendido, que el teléfono y la PC estén en la misma Wi-Fi y que el firewall permita el puerto.`,
    );
  } finally {
    clearTimeout(timer);
  }
}

export const verificarServidor = () => pedir<{ ok: true }>("/api/health");

export async function obtenerGuardado(username: string): Promise<Documento> {
  const respuesta = await pedir<{ datos: Documento }>(
    `/api/datos/${encodeURIComponent(username)}`,
  );

  return respuesta.datos;
}

export async function listarCreadores(): Promise<CreadorResumen[]> {
  const respuesta = await pedir<{ creadores: CreadorResumen[] }>(
    "/api/creadores",
  );

  return respuesta.creadores;
}

export async function analizarCreador(username: string): Promise<Documento> {
  const respuesta = await pedir<{ datos: Documento }>(
    "/api/analizar",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }),
    },
    TIMEOUT_ANALISIS_MS,
  );

  return respuesta.datos;
}

export async function enviarPropuesta(
  propuesta: PropuestaNueva,
): Promise<Propuesta> {
  const respuesta = await pedir<{ propuesta: Propuesta }>("/api/propuestas", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(propuesta),
  });

  return respuesta.propuesta;
}

export async function cargarCreador(username: string): Promise<Documento> {
  const limpio = username.trim().replace(/^@/, "");

  if (!limpio) {
    throw new ApiError("Ingresa un usuario de TikTok.");
  }

  if (USAR_GUARDADO) {
    try {
      return await obtenerGuardado(limpio);
    } catch {
      // Si no hay datos guardados, se intenta el análisis completo.
    }
  }

  return analizarCreador(limpio);
}
