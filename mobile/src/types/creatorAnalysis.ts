export type BigFiveKey =
  | 'Apertura'
  | 'Responsabilidad'
  | 'Extraversion'
  | 'Amabilidad'
  | 'Neuroticismo';

export type BigFiveResult = Partial<Record<BigFiveKey, number | null>> & {
  resumen?: string;
};

export interface CreatorProfile {
  foto_perfil?: string | null;
  siguiendo?: number | string | null;
  seguidores?: number | string | null;
  me_gusta?: number | string | null;
}

export interface CreatorVideo {
  id?: string;
  posicion?: number;
  enlace?: string;
  miniatura?: string;
  descripcion?: string;
  fecha_publicacion?: string | null;
  vistas?: number | null;
  me_gusta?: number | null;
  comentarios?: number | null;
  compartidos?: number | null;
  guardados?: number | null;
}

export interface BenfordDigit {
  digito: number;
  observados: number;
  esperados: number;
  observado_porcentaje: number | null;
  esperado_porcentaje: number;
}

export interface AudienceAudit {
  puntaje_organico: number | null;
  tamano_muestra: number;
  registros_totales: number;
  excluidos?: Record<string, number>;
  mad: number | null;
  ordenes_de_magnitud: number | null;
  distribucion: BenfordDigit[];
  advertencias: string[];
  disclaimer: string;
}

export interface BrandAffinity {
  categoria: string;
  motivo: string;
}

export interface CommercialProfile {
  tono_comunicacion?: string;
  intereses?: string[];
  afinidad_marcas?: BrandAffinity[];
}

export interface CreatorAnalysis {
  usuario: string;
  perfil: CreatorProfile;
  videos_recientes: CreatorVideo[];
  analisis_bigfive: BigFiveResult;
  analisis_bigfive_evidencia?: Record<string, unknown>;
  perfil_comercial: CommercialProfile;
  auditoria_audiencia: AudienceAudit;
}

export interface CreateProposalPayload {
  usuario_creador: string;
  marca: string;
  correo_contacto: string;
  sector: string;
  campana: string;
  presupuesto?: number | null;
  mensaje: string;
}

export interface Proposal {
  id: string;
  usuario_creador: string;
  marca: string;
  correo_contacto: string;
  sector: string;
  campana: string;
  presupuesto: number | null;
  mensaje: string;
  estado: 'pendiente' | 'aceptada' | 'rechazada' | 'completada' | 'cancelada' | string;
  created_at: string;
  updated_at: string;
}
