// Identificador público del creador en TikTok (sin la @).
declare const usernameBrand: unique symbol;
export type Username = string & { readonly [usernameBrand]: true };

// TikTok admite letras, números, guion bajo y punto; de 2 a 24 caracteres.
const USERNAME_PATTERN = /^[a-z0-9._]{2,24}$/;

/**
 * Normaliza lo que escribe el usuario ("@Foo.Bar ", "foo.bar") y lo valida.
 * Devuelve null si no es un usuario válido.
 */
export function parseUsername(raw: string): Username | null {
  const normalized = raw.trim().replace(/^@/, '').toLowerCase();
  return USERNAME_PATTERN.test(normalized) ? (normalized as Username) : null;
}
