"""Textos de consola compartidos por la CLI de truematch y main.py."""
from truematch.domain.audience_audit.organic_score import MIN_ORDERS_SPANNED, MIN_VALID_VALUES
from truematch.infrastructure.ai.prompts import LEGACY_TRAIT_KEYS


def _decimal(value, digits):
    return f"{value:.{digits}f}".replace(".", ",")


def audit_line(audit):
    """Una línea con el resultado de la auditoría de audiencia."""
    analysis = audit.analysis
    valid, orders, mad = analysis["valid_records"], analysis["orders_spanned"], analysis["mad"]
    orders_text = "—" if orders is None else str(orders)
    if audit.organic_score is not None:
        return (f"Auditoría de audiencia: puntaje orgánico {audit.organic_score.value}/100 "
                f"({valid} valores válidos, MAD {_decimal(mad, 4)}, {orders_text} órdenes de magnitud)")
    reasons = []
    if valid < MIN_VALID_VALUES:
        reasons.append(f"{valid} valores válidos de {MIN_VALID_VALUES} necesarios")
    if orders is None or orders < MIN_ORDERS_SPANNED:
        reasons.append(f"{orders_text} órdenes de magnitud de {MIN_ORDERS_SPANNED} necesarios")
    return f"Auditoría de audiencia: sin puntaje ({'; '.join(reasons)})"


def distribution_table(audit):
    """Tabla de primer dígito: observado frente a esperado por Benford."""
    lines = ["Dígito  Observados  Observado %  Esperado %"]
    for row in audit.analysis["distribution"]:
        observed = "—" if row["observed_percent"] is None else _decimal(row["observed_percent"], 1)
        lines.append(f"{row['digit']:>6}  {row['observed_count']:>10}  {observed:>11}  "
                     f"{_decimal(row['theoretical_percent'], 1):>10}")
    return "\n".join(lines)


def personality_line(personality):
    """Una línea con el Big Five: puntaje o '—' (evidencia insuficiente o puntaje inválido)."""
    parts = [f"{LEGACY_TRAIT_KEYS[t.trait]} {t.score.value if t.score else '—'}" for t in personality.big_five.traits]
    return (f"Big Five: {' · '.join(parts)} ({personality.analyzed_videos} videos analizados, "
            f"{personality.discarded_quotes} citas descartadas)")
