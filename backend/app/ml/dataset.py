"""Construcción del dataset para análisis y ML, a partir de las lecturas.

Principios (según la política del proyecto):
- NO se inventan consumos ni fechas.
- Cada punto diario se marca como OBSERVADO o INTERPOLADO.
- Se conserva trazabilidad hacia las lecturas originales.
- Las fechas "pendientes de revalidar" no se tratan como exactas: se marcan.

Procedencia de las fechas (de la columna date_confidence del CSV histórico):
- verificada: timestamp de mensaje verificado (hora real).
- confirmada: fecha confirmada por el usuario (pero sin hora real).
- inferida: fecha aproximada por secuencia.
- pendiente: "CSV previo; pendiente de revalidar".
- neon: lectura activa verificada en Neon (3036/3071/3089; hora 00:00 por migración).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass
class Reading:
    dt: datetime           # fecha + hora efectivas
    value_kwh: float       # valor acumulado del contador
    provenance: str        # verificada | confirmada | inferida | pendiente | neon
    has_real_time: bool    # True si la hora es real (no 00:00 asignada)


@dataclass
class DailyPoint:
    day: date
    kwh: float             # consumo del día
    kind: str              # "observado" | "interpolado"
    source_interval: tuple[date, date] | None  # tramo de lecturas que lo origina


def build_daily_series(readings: list[Reading]) -> list[DailyPoint]:
    """Convierte lecturas acumuladas (irregulares) en una serie diaria de
    consumo. Cuando un intervalo abarca varios días, el consumo se reparte
    de forma uniforme y esos días se marcan como INTERPOLADOS; el día que
    coincide con una lectura real se marca OBSERVADO.

    No se crean días fuera del rango cubierto por lecturas reales.
    """
    rs = sorted(readings, key=lambda r: r.dt)
    out: list[DailyPoint] = []
    for a, b in zip(rs, rs[1:]):
        d0, d1 = a.dt.date(), b.dt.date()
        total_days = (d1 - d0).days
        kwh = b.value_kwh - a.value_kwh
        if total_days <= 0 or kwh < 0:
            continue  # intradía o incoherente: se maneja aparte, no en serie diaria
        per_day = kwh / total_days
        for i in range(total_days):
            day = d0 + timedelta(days=i + 1)
            kind = "observado" if (i + 1 == total_days) else "interpolado"
            out.append(DailyPoint(day=day, kwh=round(per_day, 4), kind=kind,
                                  source_interval=(d0, d1)))
    return out


def reading_from_orm(mr) -> Reading:
    """Construye un Reading del dataset a partir de un MeterReading de la base,
    usando la metadata de procedencia ALMACENADA (source, date_confidence,
    time_known) en vez de inferirla de un CSV externo."""
    from datetime import datetime as _dt
    return Reading(
        dt=_dt.combine(mr.reading_date, mr.reading_time),
        value_kwh=float(mr.value_kwh),
        provenance=mr.date_confidence,   # verified | confirmed | inferred | pending
        has_real_time=bool(mr.time_known),
    )


def classify_counts(readings: list[Reading]) -> dict[str, int]:
    """Cuenta lecturas por procedencia y por disponibilidad de hora real."""
    counts: dict[str, int] = {}
    for r in readings:
        counts[r.provenance] = counts.get(r.provenance, 0) + 1
    counts["_con_hora_real"] = sum(1 for r in readings if r.has_real_time)
    counts["_total"] = len(readings)
    return counts


# Procedencias que SÍ sirven como verdad de referencia para evaluar un modelo.
# 'pending' queda excluida: su fecha no está confirmada, así que no debe usarse
# como ground truth. 'inferred' se considera no fiable para evaluación.
RELIABLE_PROVENANCE = {"verified", "confirmed"}


def reliable_truth_mask(daily: list[DailyPoint],
                        readings: list[Reading]) -> list[bool]:
    """Para cada día de la serie diaria, True si ese día puede usarse como
    verdad de referencia: debe ser OBSERVADO (no interpolado) y provenir de una
    lectura de procedencia fiable (verified/confirmed).

    Un día interpolado nunca es verdad de referencia. Un día cuya lectura es
    pending/inferred tampoco."""
    # mapa fecha -> procedencia de la lectura de ese día (si existe)
    prov_by_day = {r.dt.date(): r.provenance for r in readings}
    mask: list[bool] = []
    for p in daily:
        reliable = (p.kind == "observado"
                    and prov_by_day.get(p.day) in RELIABLE_PROVENANCE)
        mask.append(reliable)
    return mask
