"""Preparación del dataset ML con variables climáticas.

NO reemplaza el baseline ni el Ridge actuales. Añade, de forma aislada:
- Un mapeo de clima por intervalo a clima por día (para alinear con la serie
  diaria de consumo que ya construye dataset.build_daily_series).
- Un Ridge que admite features climáticas opcionales, reutilizando las features
  de serie del modelo actual (lag_1, ma_3, ma_7, dow) para que la única
  diferencia sea el clima.
- Un comparador de tres vías (baseline / Ridge sin clima / Ridge con clima)
  sobre LAS MISMAS muestras de evaluación, para que la comparación sea justa.

Ningún modelo se entrena ni se declara apto automáticamente: estas funciones
solo calculan métricas para una evaluación posterior hecha a mano.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
from sklearn.linear_model import Ridge

from app.ml.baseline import walk_forward_baseline
from app.ml.evaluate import metrics_masked


@dataclass
class DayWeather:
    """Clima atribuido a un día concreto (derivado del intervalo que lo cubre)."""

    temp_avg_c: float | None
    temp_max_c: float | None
    temp_min_c: float | None
    humidity_avg_pct: float | None


# Orden canónico de las features climáticas para el modelo.
WEATHER_FEATURE_NAMES = (
    "temp_avg_c",
    "temp_max_c",
    "temp_min_c",
    "humidity_avg_pct",
)


def weather_by_day(
    intervals: list[dict],
) -> dict[date, DayWeather]:
    """Mapea cada día del periodo al clima de su intervalo.

    `intervals` es una lista de dicts con: start_date, end_date (date) y los
    agregados climáticos (pueden ser None). El clima del intervalo (A, B] se
    atribuye a los días posteriores a A y hasta B inclusive, igual que la serie
    diaria de consumo, para que ambos queden alineados. Solo se atribuye clima a
    intervalos con datos disponibles (temp_avg_c no nulo)."""
    out: dict[date, DayWeather] = {}
    for it in intervals:
        if it.get("temp_avg_c") is None:
            continue  # sin datos reales: no se atribuye clima (no se inventa)
        d0: date = it["start_date"]
        d1: date = it["end_date"]
        total_days = (d1 - d0).days
        if total_days <= 0:
            continue
        dw = DayWeather(
            temp_avg_c=it.get("temp_avg_c"),
            temp_max_c=it.get("temp_max_c"),
            temp_min_c=it.get("temp_min_c"),
            humidity_avg_pct=it.get("humidity_avg_pct"),
        )
        for i in range(total_days):
            out[d0 + timedelta(days=i + 1)] = dw
    return out


def _series_features_at(series: list[float], i: int, start_day: date) -> list[float]:
    """Mismas features de serie que el Ridge actual (sin clima)."""
    lag_1 = series[i - 1]
    ma_3 = sum(series[max(0, i - 3):i]) / len(series[max(0, i - 3):i])
    ma_7 = sum(series[max(0, i - 7):i]) / len(series[max(0, i - 7):i])
    dow = (start_day + timedelta(days=i)).weekday()
    return [lag_1, ma_3, ma_7, float(dow)]


def _weather_features_at(
    day: date, day_weather: dict[date, DayWeather]
) -> list[float] | None:
    """Features climáticas del día, o None si falta alguna (no se imputan 0)."""
    dw = day_weather.get(day)
    if dw is None:
        return None
    values = [
        dw.temp_avg_c,
        dw.temp_max_c,
        dw.temp_min_c,
        dw.humidity_avg_pct,
    ]
    if any(v is None for v in values):
        return None
    return [float(v) for v in values]


def walk_forward_ridge_weather(
    series: list[float],
    start_day: date,
    day_weather: dict[date, DayWeather],
    *,
    min_train: int = 7,
    alpha: float = 1.0,
) -> tuple[list[float], list[float], list[bool]]:
    """Ridge con features de serie + clima, validación walk-forward.

    Devuelve (y_true, y_pred, usable) donde `usable[k]` indica si ese día tenía
    clima completo (tanto para entrenar como para predecir). Los días sin clima
    se predicen con el último valor conocido y se marcan usable=False, para
    poder restringir la comparación a las mismas muestras con clima.
    """
    y_true: list[float] = []
    y_pred: list[float] = []
    usable: list[bool] = []
    for i in range(min_train, len(series)):
        day_i = start_day + timedelta(days=i)
        wf_i = _weather_features_at(day_i, day_weather)

        X_tr, y_tr = [], []
        for j in range(8, i):
            day_j = start_day + timedelta(days=j)
            wf_j = _weather_features_at(day_j, day_weather)
            if wf_j is None:
                continue  # solo se entrena con días que tienen clima completo
            X_tr.append(_series_features_at(series, j, start_day) + wf_j)
            y_tr.append(series[j])

        if wf_i is None or len(X_tr) < 3:
            y_pred.append(series[i - 1])
            y_true.append(series[i])
            usable.append(False)
            continue

        model = Ridge(alpha=alpha)
        model.fit(np.array(X_tr), np.array(y_tr))
        x_i = np.array([_series_features_at(series, i, start_day) + wf_i])
        y_pred.append(float(model.predict(x_i)[0]))
        y_true.append(series[i])
        usable.append(True)
    return y_true, y_pred, usable


def compare_three_way(
    series: list[float],
    start_day: date,
    day_weather: dict[date, DayWeather],
    *,
    min_train: int = 7,
    alpha: float = 1.0,
) -> dict:
    """Compara baseline / Ridge sin clima / Ridge con clima en LAS MISMAS
    muestras (los días con clima completo). Devuelve métricas por modelo y la
    cantidad de muestras comparadas. No decide aptitud: solo mide.
    """
    from app.ml.model import walk_forward_ridge

    yb_true, yb_pred = walk_forward_baseline(series, min_train=min_train)
    yr_true, yr_pred = walk_forward_ridge(
        series, start_day, min_train=min_train, alpha=alpha
    )
    yw_true, yw_pred, usable = walk_forward_ridge_weather(
        series, start_day, day_weather, min_train=min_train, alpha=alpha
    )

    # Todas las listas arrancan en el mismo min_train, así que están alineadas
    # por índice. La máscara "usable" (clima completo) define la muestra común.
    n = min(len(yb_true), len(yr_true), len(yw_true), len(usable))
    keep = usable[:n]

    return {
        "samples_with_weather": sum(keep),
        "samples_total": n,
        "baseline": metrics_masked(yb_true[:n], yb_pred[:n], keep),
        "ridge_no_weather": metrics_masked(yr_true[:n], yr_pred[:n], keep),
        "ridge_with_weather": metrics_masked(yw_true[:n], yw_pred[:n], keep),
        "note": (
            "Comparación en las mismas muestras (días con clima completo). "
            "Ningún modelo se declara apto automáticamente."
        ),
    }
