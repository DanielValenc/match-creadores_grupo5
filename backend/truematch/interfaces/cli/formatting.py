"""Textos de consola de la CLI de truematch."""
from truematch.domain.audience_audit.organic_score import MIN_ORDERS_SPANNED, MIN_VALID_VALUES
from truematch.domain.creator_profiling.big_five import TraitStatus

STATUS_TEXT = {
    TraitStatus.INSUFFICIENT_EVIDENCE: "evidencia insuficiente",
    TraitStatus.INVALID_SCORE: "puntaje no válido",
}


def _decimal(value, digits):
    return f"{value:.{digits}f}".replace(".", ",")


def number(value):
    """Entero con separador de miles; '—' si se desconoce."""
    return "—" if value is None else f"{value:,}".replace(",", ".")


def creator_summary(creator):
    """Resumen legible del creador: una línea de perfil y una tabla con una fila por video
    (antes imprimir_resumen en main.py, que leía el archivo JSON)."""
    profile = creator.profile
    lines = [f"Perfil @{creator.username}: {number(profile.followers)} seguidores · "
             f"{number(profile.following)} siguiendo · {number(profile.likes)} me gusta"]

    columns = ("#", "Fecha", "Vistas", "Likes", "Coment.", "Compart.", "Guard.", "Descripción")
    rows = []
    for position, video in enumerate(creator.videos, start=1):
        date = video.published_at.date().isoformat() if video.published_at else "—"
        description = " ".join((video.description or "Sin descripción disponible").split())
        if len(description) > 40:
            description = description[:39] + "…"
        rows.append((str(position), date, *(number(v) for v in video.stats.values()), description))
    widths = [max([len(columns[i])] + [len(row[i]) for row in rows]) for i in range(len(columns))]

    def line(cells):
        # Números alineados a la derecha (columnas 0 y 2-6); fecha y descripción a la izquierda.
        return "  ".join(c.rjust(widths[i]) if i in (0, 2, 3, 4, 5, 6) else c.ljust(widths[i])
                         for i, c in enumerate(cells)).rstrip()

    lines += [line(columns), line(tuple("-" * w for w in widths)), *(line(row) for row in rows),
              f"{len(rows)} videos"]
    return "\n".join(lines)


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
    parts = [f"{t.trait.label} {t.score.value if t.score else '—'}" for t in personality.big_five.traits]
    return (f"Big Five: {' · '.join(parts)} ({personality.analyzed_videos} videos analizados, "
            f"{personality.discarded_quotes} citas descartadas)")


def personality_detail(personality):
    """Por rasgo: puntaje o motivo de que no haya, cobertura y citas verificadas; luego el perfil comercial."""
    lines = []
    for t in personality.big_five.traits:
        result = f"{t.score.value}/100" if t.score else STATUS_TEXT[t.status]
        lines.append(f"{t.trait.label}: {result} — evidencia en {t.supporting_videos} de "
                     f"{personality.analyzed_videos} videos ({t.evidence_coverage}%)")
        lines += [f'    «{e.quote}» (video {e.video_id})' for e in t.evidence]
    lines.append(f"Resumen (texto de la IA, no verificado): {personality.big_five.summary or '—'}")
    lines.append(f"Tono: {personality.communication_tone or '—'} · Intereses: {', '.join(personality.interests) or '—'}")
    lines += [f"Afinidad: {a['categoria']} — {a['motivo']}" for a in personality.brand_affinity]
    return "\n".join(lines)
