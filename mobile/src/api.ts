import { API_URL, TIMEOUT_ANALISIS_MS, TIMEOUT_RAPIDO_MS, USAR_GUARDADO } from './config';

// Forma del documento que devuelve el backend (legacy_document en legacy_json_repository.py).
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

export type Documento = {
  usuario: string;
  perfil: {
    foto_perfil: string;
    siguiendo: number | null;
    seguidores: number | null;
    me_gusta: number | null;
  };
  videos_recientes: Video[];
  analisis_bigfive?: BigFive;
  perfil_comercial?: {
    tono_comunicacion: string;
    intereses: string[];
    afinidad_marcas: { categoria: string; motivo: string }[];
  };
  auditoria_audiencia?: {
    puntaje_organico: number | null;
    tamano_muestra: number;
    advertencias: string[];
    disclaimer: string;
  };
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

export class ApiError extends Error {}

async function pedir<T>(ruta: string, init: RequestInit = {}, timeoutMs = TIMEOUT_RAPIDO_MS): Promise<T> {
  const controlador = new AbortController();
  const timer = setTimeout(() => controlador.abort(), timeoutMs);
  try {
    const resp = await fetch(`${API_URL}${ruta}`, { ...init, signal: controlador.signal });
    let cuerpo: any = null;
    try {
      cuerpo = await resp.json();
    } catch {
      /* respuesta sin JSON */
    }
    if (!resp.ok || !cuerpo?.ok) {
      throw new ApiError(cuerpo?.error ?? `El servidor respondió con el código ${resp.status}.`);
    }
    return cuerpo as T;
  } catch (e: any) {
    if (e instanceof ApiError) throw e;
    if (e?.name === 'AbortError') {
      throw new ApiError(`El servidor (${API_URL}) tardó demasiado en responder.`);
    }
    throw new ApiError(
      `No se pudo conectar con el servidor (${API_URL}). Comprueba que Flask esté encendido, ` +
        'que el teléfono y la PC estén en la misma Wi-Fi y que el firewall permita el puerto.'
    );
  } finally {
    clearTimeout(timer);
  }
}

export const verificarServidor = () => pedir<{ ok: true }>('/api/health');

export async function obtenerGuardado(username: string): Promise<Documento> {
  const r = await pedir<{ datos: Documento }>(`/api/datos/${encodeURIComponent(username)}`);
  return r.datos;
}

export async function listarCreadores(): Promise<CreadorResumen[]> {
  const r = await pedir<{ creadores: CreadorResumen[] }>('/api/creadores');
  return r.creadores;
}

export async function enviarPropuesta(propuesta: PropuestaNueva): Promise<Propuesta> {
  const r = await pedir<{ propuesta: Propuesta }>('/api/propuestas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(propuesta),
  });
  return r.propuesta;
}

export async function analizarCreador(username: string): Promise<Documento> {
  const r = await pedir<{ datos: Documento }>(
    '/api/analizar',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    },
    TIMEOUT_ANALISIS_MS
  );
  return r.datos;
}

// Punto de entrada de las pantallas.
export async function cargarCreador(username: string): Promise<Documento> {
  if (USAR_GUARDADO) {
    try {
      return await obtenerGuardado(username);
    } catch {
      /* no hay datos guardados (o el servidor no responde): se intenta el análisis completo */
    }
  }
  return analizarCreador(username);
}
