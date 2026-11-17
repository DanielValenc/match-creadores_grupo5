"""Puerto CreatorSource: de dónde se obtiene el perfil público y los videos de un creador."""
from abc import ABC, abstractmethod

from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.username import Username


class CreatorSource(ABC):
    @abstractmethod
    def fetch(self, username: Username) -> Creator:
        """Devuelve el Creator con su perfil público y sus videos recientes.

        Lanza una excepción si no se puede obtener; nunca devuelve un perfil vacío o con ceros inventados.
        """
