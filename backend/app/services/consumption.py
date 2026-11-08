"""Cálculo de consumo entre lecturas. Funciones puras, fáciles de testear."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# Número que puede venir como float (cálculo puro) o Decimal (desde la base).
Num = float | Decimal


def _to_decimal(v: Num) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


@dataclass
class Interval:
    start_date: date
    end_date: date
    days: int
    kwh: float


def intervals_from_readings(readings: list[tuple[date, Num]]) -> list[Interval]:
    """Recibe lecturas (fecha, valor_acumulado) ORDENADAS por fecha ascendente.
    Devuelve el consumo de cada tramo entre lecturas consecutivas.

    El contador es acumulado: el consumo de un tramo es la diferencia de
    valores. Una diferencia negativa significa datos incoherentes y se omite.
    """
    out: list[Interval] = []
    for (d0, v0), (d1, v1) in zip(readings, readings[1:]):
        days = (d1 - d0).days
        kwh = float(v1) - float(v0)
        # days < 0 o kwh < 0 => datos incoherentes, se omite.
        # days == 0 (dos lecturas el mismo día) SÍ cuenta su consumo.
        if days < 0 or kwh < 0:
            continue
        out.append(Interval(start_date=d0, end_date=d1, days=days, kwh=kwh))
    return out


def total_kwh(intervals: list[Interval]) -> float:
    return sum(i.kwh for i in intervals)


def total_days(intervals: list[Interval]) -> int:
    return sum(i.days for i in intervals)


def span_days(intervals: list[Interval]) -> int:
    """Días reales cubiertos: desde el inicio del primer tramo al fin del
    último. Evita contar de más cuando hay varias lecturas el mismo día
    (tramos intradía con days=0)."""
    if not intervals:
        return 0
    return (intervals[-1].end_date - intervals[0].start_date).days


def avg_daily_kwh(intervals: list[Interval]) -> float:
    d = span_days(intervals)
    return total_kwh(intervals) / d if d > 0 else 0.0


def estimate_cost(kwh: Num, price_per_kwh: Num) -> float:
    """Costo con redondeo correcto a 2 decimales (ROUND_HALF_UP)."""
    cents = (_to_decimal(kwh) * _to_decimal(price_per_kwh)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return float(cents)


def cost_by_period(
    intervals: list[Interval], price_for: "PriceLookup"
) -> float:
    """Costo total cobrando cada tramo con la tarifa vigente en su fecha de
    inicio. price_for(date) -> precio por kWh. Base de la regla 7."""
    total = Decimal("0")
    for itv in intervals:
        price = _to_decimal(price_for(itv.start_date))
        total += _to_decimal(itv.kwh) * price
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def monthly_projection(avg_daily: float) -> float:
    """Proyección estadística simple: promedio diario * 30. NO es ML."""
    return round(avg_daily * 30, 3)


@dataclass
class PeriodConsumption:
    start: date
    end: date
    kwh: float
    estimated: bool          # True si hubo interpolación en algún borde
    estimated_fraction: float  # proporción del kWh que proviene de interpolación
    sufficient: bool         # False si no hay lecturas para un cálculo razonable
    note: str


def consumption_between(
    readings: list[tuple[date, Num]], start: date, end: date
) -> PeriodConsumption:
    """Consumo en [start, end] a partir de lecturas acumuladas (fecha, valor)
    ORDENADAS. Los tramos que cruzan un borde se reparten proporcionalmente por
    días (interpolación), y esa porción se marca como estimada.

    Si no hay lecturas que cubran el período de forma razonable, devuelve
    sufficient=False sin inventar consumo.
    """
    if end < start:
        return PeriodConsumption(start, end, 0.0, False, 0.0, False,
                                 "Rango inválido: end < start.")
    pairs = [(d, float(v)) for d, v in readings]
    pairs.sort(key=lambda x: x[0])

    # ¿hay lecturas que solapen el período?
    covering = [p for p in pairs if p[0] <= end]
    if len(pairs) < 2 or not covering or pairs[0][0] > end or pairs[-1][0] < start:
        return PeriodConsumption(start, end, 0.0, False, 0.0, False,
                                 "Información insuficiente: no hay lecturas que "
                                 "cubran el período.")

    total = 0.0
    estimated = 0.0
    any_interp = False
    span = (end - start).days + 1
    for (d0, v0), (d1, v1) in zip(pairs, pairs[1:]):
        days = (d1 - d0).days
        kwh = v1 - v0
        if days <= 0 or kwh < 0:
            continue
        # solapamiento del tramo [d0,d1] con [start,end]
        ov_start = max(d0, start)
        ov_end = min(d1, end)
        ov_days = (ov_end - ov_start).days
        if ov_days <= 0:
            continue
        frac = ov_days / days
        part = kwh * frac
        total += part
        # si el tramo no está enteramente dentro del período, la parte es estimada
        if d0 < start or d1 > end:
            estimated += part
            any_interp = True

    if total == 0.0:
        return PeriodConsumption(start, end, 0.0, False, 0.0, False,
                                 "Información insuficiente para el período.")

    est_frac = round(estimated / total, 4) if total else 0.0
    return PeriodConsumption(
        start=start, end=end, kwh=round(total, 3),
        estimated=any_interp, estimated_fraction=est_frac, sufficient=True,
        note=("Incluye interpolación proporcional en los bordes del período."
              if any_interp else "Cálculo sobre tramos completos."),
    )


def cost_between(
    period: PeriodConsumption, intervals: list[Interval], price_for: "PriceLookup"
) -> float:
    """Costo del período usando la tarifa vigente en el inicio de cada tramo que
    cae dentro, proporcional al solapamiento. Reusa la política histórica."""
    if not period.sufficient:
        return 0.0
    total = Decimal("0")
    for itv in intervals:
        ov_start = max(itv.start_date, period.start)
        ov_end = min(itv.end_date, period.end)
        ov_days = (ov_end - ov_start).days
        if ov_days <= 0 or itv.days <= 0:
            continue
        frac = Decimal(ov_days) / Decimal(itv.days)
        price = _to_decimal(price_for(itv.start_date))
        total += _to_decimal(itv.kwh) * frac * price
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# Tipo del callback de precio por fecha. Se importa perezoso para no crear
# dependencia circular con los servicios de base de datos.
from typing import Callable  # noqa: E402

PriceLookup = Callable[[date], Num]
