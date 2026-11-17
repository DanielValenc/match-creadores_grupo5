// URL del backend Flask de la PC. Se define en mobile/.env (ver .env.example):
//   EXPO_PUBLIC_API_URL=http://192.168.18.9:5000
// Tras cambiar el .env hay que reiniciar Expo con:  npx expo start -c
export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:5000"
).replace(/\/+$/, "");

// Modo desarrollo: si es '1', se usa primero el resultado ya guardado (datos_<usuario>.json)
// y solo se extrae de TikTok cuando no existe. Útil para probar la app sin abrir TikTok.
export const USAR_GUARDADO = process.env.EXPO_PUBLIC_USAR_GUARDADO === "1";

// La extracción de TikTok (con posible Captcha) puede tardar bastante.
export const TIMEOUT_ANALISIS_MS = 240_000;
export const TIMEOUT_RAPIDO_MS = 8_000;
