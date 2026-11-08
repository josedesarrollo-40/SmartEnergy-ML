"""Métricas de evaluación y validación temporal walk-forward."""

from __future__ import annotations

import math


def mae(y_true: list[float], y_pred: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def rmse(y_true: list[float], y_pred: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / len(y_true))


def mape(y_true: list[float], y_pred: list[float]) -> float | None:
    """MAPE en %. None si algún valor real es 0 (no aplicable)."""
    if any(a == 0 for a in y_true):
        return None
    return 100 * sum(abs((a - b) / a) for a, b in zip(y_true, y_pred)) / len(y_true)


def metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float | None]:
    if not y_true:
        return {"MAE": None, "RMSE": None, "MAPE": None, "n": 0}
    return {"MAE": round(mae(y_true, y_pred), 4),
            "RMSE": round(rmse(y_true, y_pred), 4),
            "MAPE": (round(m, 2) if (m := mape(y_true, y_pred)) is not None else None),
            "n": len(y_true)}


def metrics_masked(
    y_true: list[float], y_pred: list[float], keep: list[bool]
) -> dict[str, float | None]:
    """Calcula métricas solo en los días marcados True en `keep`.
    Sirve para evaluar únicamente los días OBSERVADOS, aunque el modelo haya
    usado la serie completa (con interpolados) para construir sus lags."""
    yt = [a for a, k in zip(y_true, keep) if k]
    yp = [b for b, k in zip(y_pred, keep) if k]
    return metrics(yt, yp)
