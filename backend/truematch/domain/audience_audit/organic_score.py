"""OrganicScore: qué parte de la audiencia parece real, de 0 a 100 (README §6.4).

Es una política propia de este proyecto sobre el análisis descriptivo de benford.py,
que por diseño no clasifica cuentas. Ver docs/plan-backend.md, «Conciliación».
"""
from dataclasses import dataclass

# Constantes del dominio que el equipo puede ajustar.
MIN_VALID_VALUES = 110      # con menos, algún recuento esperado de Benford es menor que 5
MIN_ORDERS_SPANNED = 2      # Benford necesita valores que abarquen varios órdenes de magnitud
MAD_AT_ZERO_SCORE = 0.03    # MAD a partir de la cual el puntaje es 0


@dataclass(frozen=True)
class OrganicScore:
    value: int

    def __post_init__(self):
        if isinstance(self.value, bool) or not isinstance(self.value, int) or not 0 <= self.value <= 100:
            raise ValueError("OrganicScore debe ser un entero entre 0 y 100.")

    @classmethod
    def from_mad(cls, mad):
        """round(100 × max(0, 1 − MAD / MAD_AT_ZERO_SCORE))."""
        if mad is None or mad < 0:
            raise ValueError("La MAD debe ser un número no negativo.")
        return cls(round(100 * max(0.0, 1 - mad / MAD_AT_ZERO_SCORE)))
