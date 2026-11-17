"""TraitEvidence: cita literal de la descripción de un video que respalda un rasgo del Big Five."""
from dataclasses import dataclass
import unicodedata


def canonical_text(value):
    """Solo composición Unicode (NFC) y espacios; nunca coincidencias aproximadas de palabras o puntuación.

    Origen: media-scraper, backend/semantic_analysis.py (commit a3ef81d), función canonical_text.
    """
    return ' '.join(unicodedata.normalize('NFC', value).split())


def is_literal_quote(quote, text):
    """True si la cita, normalizada, aparece tal cual dentro del texto normalizado."""
    if not isinstance(quote, str) or not isinstance(text, str):
        return False
    normalized = canonical_text(quote)
    return bool(normalized) and normalized in canonical_text(text)


@dataclass(frozen=True)
class TraitEvidence:
    video_id: str
    quote: str

    def __post_init__(self):
        if not isinstance(self.video_id, str) or not self.video_id:
            raise ValueError("La evidencia necesita el ID del video citado.")
        if not isinstance(self.quote, str) or not canonical_text(self.quote):
            raise ValueError("La evidencia necesita una cita no vacía.")


def verify_quotes(claims, descriptions):
    """Separa las citas verificables de las inventadas.

    claims: pares (video_id o None, cita) tal como los propone la IA.
    descriptions: {video_id: descripción} de los videos que se le enviaron.
    Devuelve (evidencias válidas sin duplicados, cantidad de citas descartadas).
    """
    valid, seen, discarded = [], set(), 0
    for video_id, quote in claims:
        text = descriptions.get(video_id) if video_id is not None else None
        if text is None or not is_literal_quote(quote, text):
            discarded += 1
            continue
        key = (video_id, canonical_text(quote))
        if key not in seen:
            seen.add(key)
            valid.append(TraitEvidence(video_id, canonical_text(quote)))
    return tuple(valid), discarded
