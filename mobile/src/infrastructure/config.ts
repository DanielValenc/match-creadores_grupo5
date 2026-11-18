// Configuración leída de variables EXPO_PUBLIC_* (ver mobile/.env.example).
// Expo las incrusta al compilar, por eso se leen con acceso estático a process.env.X.

function readApiUrl(): string | null {
  const raw = process.env.EXPO_PUBLIC_API_URL?.trim();
  return raw ? raw.replace(/\/+$/, '') : null;
}

function readUseMock(): boolean {
  return process.env.EXPO_PUBLIC_USE_MOCK?.trim().toLowerCase() === 'true';
}

export const config = {
  /** URL base de la web/API, sin barra final. null si no está configurada. */
  apiUrl: readApiUrl(),
  /** true = usar MockCreatorRepository en lugar de la API. */
  useMock: readUseMock(),
} as const;
