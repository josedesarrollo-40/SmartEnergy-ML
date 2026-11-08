"""Predicción de referencia (baseline): media móvil.

No es Machine Learning. Es la vara contra la que se compara cualquier modelo:
un modelo solo aporta valor si supera a este baseline.
"""

from __future__ import annotations


def moving_average_forecast(history: list[float], window: int = 7) -> float:
    """Predice el próximo valor como la media de los últimos `window` días."""
    w = history[-window:] if len(history) >= window else history
    return sum(w) / len(w) if w else 0.0


def walk_forward_baseline(series: list[float], window: int = 7,
                          min_train: int = 7) -> tuple[list[float], list[float]]:
    """Walk-forward: para cada día desde min_train, predice con la media móvil
    de los días anteriores y compara con el real. Devuelve (reales, predichos).
    Nunca usa información futura."""
    y_true: list[float] = []
    y_pred: list[float] = []
    for i in range(min_train, len(series)):
        pred = moving_average_forecast(series[:i], window)
        y_pred.append(pred)
        y_true.append(series[i])
    return y_true, y_pred
