"""Reglas de validación de lecturas del contador."""

import math
from datetime import date, datetime, time


class ReadingValidationError(ValueError):
    """La lectura nueva es incoherente con el historial o con sus propias
    reglas de valor."""


MIDNIGHT = time(0, 0, 0)


def _combine(d: date, t: time | None) -> datetime:
    return datetime.combine(d, t or MIDNIGHT)


def validate_new_reading(
    new_date: date,
    new_value: float,
    prev_date: date | None,
    prev_value: float | None,
    new_time: time | None = None,
    prev_time: time | None = None,
) -> None:
    """Valida una lectura nueva.

    Reglas:
    - El valor debe ser un número finito y no negativo.
    - El contador solo sube: una lectura posterior no puede valer menos que la
      anterior.
    - El instante (fecha + hora) debe ser POSTERIOR al de la última lectura.
      Se permiten varias lecturas el mismo día si la hora avanza. Un instante
      igual lo refuerza además la UNIQUE (fecha, hora) de la base.
    """
    if not math.isfinite(new_value):
        raise ReadingValidationError("El valor debe ser un número finito.")
    if new_value < 0:
        raise ReadingValidationError("El valor no puede ser negativo.")

    if prev_date is None or prev_value is None:
        return

    new_dt = _combine(new_date, new_time)
    prev_dt = _combine(prev_date, prev_time)

    if new_dt <= prev_dt:
        raise ReadingValidationError(
            "La fecha y hora deben ser posteriores a la última lectura registrada."
        )
    if new_value < prev_value:
        raise ReadingValidationError(
            "El valor del contador no puede ser menor que la lectura anterior."
        )
