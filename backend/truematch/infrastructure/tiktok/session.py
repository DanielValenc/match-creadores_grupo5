# Origen: media-scraper, rama feature/setup-inicial, commit a3ef81d2e533d0c9e58e144ee6c4c863a43961cc,
# archivo backend/session.py (ver docs/plan-backend.md, paso 7). Cambios respecto del original:
#   - fcntl.flock -> filelock.FileLock, para que el bloqueo funcione también en Windows.
#   - os.fchmod -> Path.chmod (os.fchmod no existe en Windows).
#   - Carpeta privada: <raíz del repositorio>/.truematch (antes .media-scraper).
"""Perfil local dedicado de Chromium con un bloqueo entre procesos (Linux, macOS y Windows)."""

from contextlib import contextmanager
import os
from pathlib import Path

from filelock import FileLock, Timeout
from playwright.sync_api import Error as PlaywrightError, sync_playwright

# backend/truematch/infrastructure/tiktok/session.py -> parents[4] es la raíz del repositorio.
PRIVATE_DIR = Path(__file__).resolve().parents[4] / ".truematch"


class SessionBusyError(RuntimeError):
    pass


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)  # En Windows solo afecta al atributo de solo lectura.
    return path


@contextmanager
def profile_lock():
    root = private_directory(PRIVATE_DIR)
    lock_path = root / "session.lock"
    # El archivo de bloqueo se crea solo para el usuario actual.
    os.close(os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600))
    lock_path.chmod(0o600)
    lock = FileLock(str(lock_path))
    try:
        lock.acquire(timeout=0)
    except Timeout:
        raise SessionBusyError(
            "La sesión está en uso. Espera a que termine la consulta "
            "o cierra la configuración inicial."
        ) from None
    try:
        yield private_directory(root / "chromium")
    finally:
        lock.release()


@contextmanager
def persistent_context(*, headless=True):
    with profile_lock() as profile:
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile), headless=headless,
                    accept_downloads=False,
                )
                try:
                    yield context
                finally:
                    context.close()
        except PlaywrightError:
            # Driver errors can include URLs or private profile information.
            raise RuntimeError(
                "No se pudo cargar TikTok o iniciar Chromium. Comprueba la conexión, "
                "la instalación de Chromium y configura la sesión si es necesario."
            ) from None


def configure_session():
    with persistent_context(headless=False) as context:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded", timeout=30000)
        print("Inicia sesión manualmente en tu cuenta dentro de Chromium.")
        print("Si TikTok pide una verificación, resuélvela manualmente o cancela.")
        input("Cuando hayas terminado, pulsa ENTER aquí para guardar y cerrar: ")
