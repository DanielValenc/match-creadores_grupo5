"""Propuestas de colaboración guardadas en propuestas.json (junto a los datos_<usuario>.json).

Solución provisional: el dominio brand_matching (README, «Envío de propuestas») todavía no modela la propuesta.
La escritura es atómica (archivo temporal + os.replace) y un bloqueo por proceso evita que dos peticiones
simultáneas se pisen; no protege contra varios procesos escribiendo a la vez.
"""
import json
import os
from pathlib import Path
import tempfile
import threading


class ProposalStorageError(RuntimeError):
    """No se pudo leer o escribir propuestas.json."""


class JsonProposalRepository:
    _lock = threading.Lock()  # compartido por todas las instancias: la web crea una por petición

    def __init__(self, directory="."):
        self.path = Path(directory) / "propuestas.json"

    def _read(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ProposalStorageError("No se pudo leer propuestas.json.") from error
        if not isinstance(data, list):
            raise ProposalStorageError("propuestas.json no contiene una lista válida.")
        return data

    def _write(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=".propuestas.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(items, stream, ensure_ascii=False, indent=2)
            os.replace(temporary, self.path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

    def list(self, creator=None):
        """Propuestas de la más reciente a la más antigua; si se indica creator, solo las de ese usuario."""
        with self._lock:
            items = self._read()
        if creator:
            items = [p for p in items if str(p.get("usuario_creador", "")).casefold() == creator.casefold()]
        return sorted(items, key=lambda p: p.get("created_at", ""), reverse=True)

    def get(self, proposal_id):
        with self._lock:
            return next((p for p in self._read() if p.get("id") == proposal_id), None)

    def add(self, proposal):
        with self._lock:
            items = self._read()
            items.append(proposal)
            try:
                self._write(items)
            except OSError as error:
                raise ProposalStorageError("No se pudo guardar la propuesta.") from error
