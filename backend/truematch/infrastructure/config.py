"""Configuración de TrueMatch AI: rutas de datos y credenciales de Groq."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv  # opcional, si tienes python-dotenv instalado
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # backend/.env
except ImportError:
    pass


class ConfigError(RuntimeError):
    """Falta configuración obligatoria (p. ej. GROQ_API_KEY)."""


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    groq_api_key: str | None
    groq_model: str

    def require_groq_api_key(self) -> str:
        if not self.groq_api_key:
            raise ConfigError(
                "Falta GROQ_API_KEY. Añádela a backend/.env o expórtala en el entorno."
            )
        return self.groq_api_key


def load_settings() -> Settings:
    base = Path(__file__).resolve().parents[2]  # .../backend/
    data_dir = Path(os.getenv("TRUEMATCH_DATA_DIR", base)).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=data_dir,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    )