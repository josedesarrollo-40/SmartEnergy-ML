"""Servicio de calidad de datos de lecturas.

Reporta, sin modificar nada, el estado del histórico: días observados,
días estimados por interpolación, días sin cobertura, fechas/horas pendientes
de validar e intervalos irregulares.

Principio: un día interpolado NO es una medición real, y un intervalo largo NO
se asume como consumo uniforme observado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.models.reading import MeterReading


@dataclass
class QualityReport:
    total_readings: int
    first_date: date | None
    last_date: date | None
    span_days: int
    observed_days: int          # días con una lectura real
    interpolated_days: int      # días dentro de un hueco (sin lectura propia)
    missing_days: int           # días del rango sin cobertura (igual a interpolated aquí)
    time_known_count: int       # lecturas con hora real
    confidence_counts: dict[str, int] = field(default_factory=dict)
    source_counts: dict[str, int] = field(default_factory=dict)
    irregular_intervals: list[dict] = field(default_factory=list)
    pending_or_inferred: int = 0


def _irregular(intervals_days: list[int]) -> bool:
    return False


def build_quality_report(
    readings: list[MeterReading], regular_days: int = 1, tolerance: float = 1.5
) -> QualityReport:
    """Construye el reporte de calidad a partir de las lecturas (ya ordenadas
    o no). regular_days = cadencia esperada; un intervalo se marca irregular si
    supera regular_days * tolerance."""
    rs = sorted(readings, key=lambda r: (r.reading_date, r.reading_time))
    n = len(rs)
    if n == 0:
        return QualityReport(0, None, None, 0, 0, 0, 0, 0)

    first = rs[0].reading_date
    last = rs[-1].reading_date
    span = (last - first).days

    # días con lectura real (observados): fechas distintas que tienen lectura
    observed_dates = {r.reading_date for r in rs}
    observed_days = len(observed_dates)

    # días del rango sin lectura propia -> estimados/sin cobertura
    all_days = {first + timedelta(days=i) for i in range(span + 1)}
    missing = sorted(all_days - observed_dates)
    interpolated_days = len(missing)

    # confianza y origen
    conf: dict[str, int] = {}
    src: dict[str, int] = {}
    time_known = 0
    pending_inferred = 0
    for r in rs:
        conf[r.date_confidence] = conf.get(r.date_confidence, 0) + 1
        src[r.source] = src.get(r.source, 0) + 1
        if r.time_known:
            time_known += 1
        if r.date_confidence in ("pending", "inferred"):
            pending_inferred += 1

    # intervalos irregulares
    irregular: list[dict] = []
    for a, b in zip(rs, rs[1:]):
        d = (b.reading_date - a.reading_date).days
        if d > regular_days * tolerance:
            irregular.append(
                {"from": a.reading_date.isoformat(),
                 "to": b.reading_date.isoformat(),
                 "days": d}
            )

    return QualityReport(
        total_readings=n,
        first_date=first,
        last_date=last,
        span_days=span,
        observed_days=observed_days,
        interpolated_days=interpolated_days,
        missing_days=interpolated_days,
        time_known_count=time_known,
        confidence_counts=conf,
        source_counts=src,
        irregular_intervals=irregular,
        pending_or_inferred=pending_inferred,
    )
