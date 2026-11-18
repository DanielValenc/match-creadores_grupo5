"""OrganicScore: qué parte de la audiencia parece real, de 0 a 100 (README §6.4).

Es una política propia de este proyecto sobre el análisis descriptivo de benford.py,
que por diseño no clasifica cuentas. Ver docs/plan-backend.md, «Conciliación».
"""
from dataclasses import dataclass
import math

# Constantes del dominio que el equipo puede ajustar.
MIN_VALID_VALUES = 110      # con menos, algún recuento esperado de Benford es menor que 5
MIN_ORDERS_SPANNED = 2      # Benford necesita valores que abarquen varios órdenes de magnitud

# MAD que se espera solo por azar cuando los datos siguen Benford: E[MAD] ≈ MAD_NOISE_COEFFICIENT / √n.
# Aproximación normal: p̂_d − p_d ~ N(0, p_d(1 − p_d)/n), con E|N(0, σ²)| = σ·√(2/π), luego
#   E[MAD] = (1/9) · Σ_d √(2/π) · √(p_d(1 − p_d)) / √n,  con p_d = log10(1 + 1/d).
# Comprobada con 20 000 simulaciones por tamaño (semilla 20261117, random.Random):
# para n = 110, 150, 300, 500, 1000 y 2000 la media simulada difiere < 0,2 % de la aproximación.
MAD_NOISE_COEFFICIENT = math.sqrt(2 / math.pi) * math.fsum(
    math.sqrt(p * (1 - p)) for p in (math.log10(1 + 1 / d) for d in range(1, 10))) / 9   # ≈ 0,2348

# El puntaje depende del cociente MAD observada / MAD esperada por azar. En las mismas simulaciones,
# con datos que siguen Benford, ese cociente casi no depende de n: percentil 95 ≈ 1,49,
# percentil 99 ≈ 1,73, percentil 99,9 ≈ 2,0. Primeros dígitos uniformes dan un cociente ≈ 2,7 con
# n = 110 y crecen con √n.
FULL_SCORE_RATIO = 1.5      # hasta aquí la desviación es la del azar: puntaje 100
ZERO_SCORE_RATIO = 2.5      # desde aquí la desviación supera con holgura el azar: puntaje 0


def expected_mad(n):
    """MAD esperada solo por azar en una muestra de n valores que siguen Benford."""
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("El tamaño de muestra debe ser un entero positivo.")
    return MAD_NOISE_COEFFICIENT / math.sqrt(n)


@dataclass(frozen=True)
class OrganicScore:
    value: int

    def __post_init__(self):
        if isinstance(self.value, bool) or not isinstance(self.value, int) or not 0 <= self.value <= 100:
            raise ValueError("OrganicScore debe ser un entero entre 0 y 100.")

    @classmethod
    def from_mad(cls, mad, n):
        """Con r = MAD / expected_mad(n): 100 si r ≤ FULL_SCORE_RATIO, 0 si r ≥ ZERO_SCORE_RATIO
        y lineal entre ambos."""
        if mad is None or mad < 0:
            raise ValueError("La MAD debe ser un número no negativo.")
        ratio = mad / expected_mad(n)
        fraction = (ratio - FULL_SCORE_RATIO) / (ZERO_SCORE_RATIO - FULL_SCORE_RATIO)
        return cls(round(100 * (1 - min(1.0, max(0.0, fraction)))))
