/** Configuración central del cliente móvil TrueMatch. */

// En un teléfono físico, usa la IPv4 Wi-Fi de la computadora donde corre Flask.
// El valor de .env tiene prioridad sobre este fallback.
export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:5000"
)
  .trim()
  .replace(/\/+$/, "");

export const USAR_GUARDADO = process.env.EXPO_PUBLIC_USAR_GUARDADO === "1";

// El scraping puede tardar varios minutos, especialmente si requiere login/CAPTCHA.
export const TIMEOUT_ANALISIS_MS = 720_000;
export const TIMEOUT_RAPIDO_MS = 8_000;
