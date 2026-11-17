"""Configuración de TrueMatch AI: archivo .env, clave y modelo de Groq, carpeta de datos y carpeta privada.

Es el único lugar que calcula la raíz del repositorio. Variables de entorno (o .env en la raíz):
    GROQ_API_KEY            clave de Groq (obligatoria para el análisis de personalidad)
    GROQ_MODEL              modelo de Groq (opcional)
    TRUEMATCH_HOME          raíz del proyecto (opcional; por defecto, la del repositorio)
    TRUEMATCH_DATA_DIR      carpeta de los datos_<usuario>.json (opcional; por defecto, TRUEMATCH_HOME)
    TRUEMATCH_PRIVATE_DIR   carpeta privada de la sesión de Chromium (opcional; por defecto, TRUEMATCH_HOME/.truematch)
"""
from dataclasses import dataclass
import os
from pathlib import Path

# backend/truematch/infrastructure/config.py -> parents[3] es la raíz del repositorio.
DEFAULT_HOME = Path(__file__).resolve().parents[3]
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"


class ConfigError(RuntimeError):
    """Falta una configuración obligatoria."""


def _load_dotenv(home):
    """Carga <home>/.env si python-dotenv está instalado; las variables ya definidas tienen prioridad."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(home / ".env")


@dataclass(frozen=True)
class Settings:
    home: Path
    data_dir: Path
    private_dir: Path
    groq_api_key: str | None
    groq_model: str

    def require_groq_api_key(self):
        if not self.groq_api_key:
            raise ConfigError(
                "No se encontró la variable de entorno GROQ_API_KEY.\n"
                "  Windows (CMD):  set GROQ_API_KEY=tu_clave\n"
                "  Mac / Linux:    export GROQ_API_KEY=\"tu_clave\"\n"
                f"  O crea un archivo {self.home / '.env'} con: GROQ_API_KEY=tu_clave"
            )
        return self.groq_api_key


def load_settings():
    """Lee la configuración del entorno en el momento de la llamada.

    Las variables de .env se cargan una vez por proceso: para que un cambio en .env se aplique, reinicia la web.
    """
    home = Path(os.getenv("TRUEMATCH_HOME") or DEFAULT_HOME).resolve()
    _load_dotenv(home)
    return Settings(
        home=home,
        data_dir=Path(os.getenv("TRUEMATCH_DATA_DIR") or home).resolve(),
        private_dir=Path(os.getenv("TRUEMATCH_PRIVATE_DIR") or home / ".truematch").resolve(),
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        groq_model=os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL,
    )
