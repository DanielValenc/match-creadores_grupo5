// Datos públicos del perfil. null = el dato no se pudo extraer (no es lo mismo que 0).
export interface PublicProfile {
  readonly avatarUrl: string | null;
  readonly following: number | null;
  readonly followers: number | null;
  readonly likes: number | null;
}
