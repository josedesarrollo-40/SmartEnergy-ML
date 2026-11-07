"""Reglas de validación de lecturas del contador."""

import math
from datetime import date


class ReadingValidationError(ValueError):
    """La lectura nueva es incoherente con el historial o con sus propias
    reglas de valor."""


def validate_new_reading(
    new_date: date,
    new_value: float,
    prev_date: date | None,
    prev_value: float | None,
) -> None:
    """Valida una lectura nueva.

    Reglas:
    - El valor debe ser un número finito y no negativo.
    - El contador solo sube: una lectura posterior no puede valer menos que la
      anterior.
    - La fecha debe ser posterior a la última lectura (no igual, no anterior).
      La fecha repetida la refuerza además la UNIQUE de la base.
    """
    if not math.isfinite(new_value):
        raise ReadingValidationError("El valor debe ser un número finito.")
    if new_value < 0:
        raise ReadingValidationError("El valor no puede ser negativo.")

    if prev_date is None or prev_value is None:
        return

    if new_date <= prev_date:
        raise ReadingValidationError(
            "La fecha debe ser posterior a la última lectura registrada."
        )
    if new_value < prev_value:
        raise ReadingValidationError(
            "El valor del contador no puede ser menor que la lectura anterior."
        )
