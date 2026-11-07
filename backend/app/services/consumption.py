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
        if days <= 0 or kwh < 0:
            continue
        out.append(Interval(start_date=d0, end_date=d1, days=days, kwh=kwh))
    return out


def total_kwh(intervals: list[Interval]) -> float:
    return sum(i.kwh for i in intervals)


def total_days(intervals: list[Interval]) -> int:
    return sum(i.days for i in intervals)


def avg_daily_kwh(intervals: list[Interval]) -> float:
    d = total_days(intervals)
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


# Tipo del callback de precio por fecha. Se importa perezoso para no crear
# dependencia circular con los servicios de base de datos.
from typing import Callable  # noqa: E402

PriceLookup = Callable[[date], Num]
