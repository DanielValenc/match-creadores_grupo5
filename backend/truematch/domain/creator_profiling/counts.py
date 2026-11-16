"""Validación compartida de contadores públicos: entero no negativo, o None si no se conoce."""


def optional_count(name, value):
    """Devuelve value si es None o un int >= 0. Nunca convierte ni rellena valores desconocidos."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} debe ser un entero no negativo o None.")
    return value
