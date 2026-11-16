"""Username: identificador del creador en TikTok, sin @ (README §6.6, regla 1)."""
from dataclasses import dataclass
import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9._]{2,24}")


class InvalidUsername(ValueError):
    """El texto recibido no es un usuario de TikTok válido."""


@dataclass(frozen=True)
class Username:
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str) or not USERNAME_PATTERN.fullmatch(self.value):
            raise InvalidUsername(
                "El usuario debe tener de 2 a 24 caracteres: letras, números, punto o guion bajo, sin @."
            )
        if set(self.value) == {"."}:
            raise InvalidUsername("El usuario no puede estar formado solo por puntos.")

    @classmethod
    def parse(cls, raw):
        """Acepta 'usuario' o '@usuario' (con espacios alrededor) y devuelve el Username sin @."""
        if not isinstance(raw, str):
            raise InvalidUsername("El usuario debe ser un texto.")
        return cls(raw.strip().removeprefix("@"))

    @property
    def key(self):
        """Forma para comparar usuarios: TikTok no distingue mayúsculas de minúsculas."""
        return self.value.casefold()

    def __str__(self):
        return self.value
