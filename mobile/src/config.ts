// URL del backend Flask.
// Se configura en el archivo .env de la aplicación Mobile.
export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:5000"
).replace(/\/+$/, "");

// Si es '1', intenta recuperar primero los resultados guardados.
// Si es '0', ejecuta un análisis nuevo de TikTok.
export const USAR_GUARDADO = process.env.EXPO_PUBLIC_USAR_GUARDADO === "1";

// El análisis puede tardar bastante por TikTok, CAPTCHA y Groq.
// 12 minutos para permitir la verificación manual de hasta 10 minutos.
export const TIMEOUT_ANALISIS_MS = 720_000;

// Tiempo máximo para consultas rápidas.
export const TIMEOUT_RAPIDO_MS = 8_000;
