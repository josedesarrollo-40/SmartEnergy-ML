"""Modelo experimental Ridge y su validación walk-forward.

Features (justificadas por los datos disponibles, todas derivadas de la propia
serie, sin datos externos):
- lag_1: consumo del día anterior.
- ma_3: media de los últimos 3 días.
- ma_7: media de los últimos 7 días.
- dow: día de la semana (0-6).

Validación walk-forward con TimeSeriesSplit implícito (entrenar con el pasado,
predecir el día siguiente). Sin fuga de información: las features del día i solo
usan días < i.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
from sklearn.linear_model import Ridge


def _features_at(series: list[float], i: int, start_day: date) -> list[float]:
    """Features para predecir el día i, usando solo días < i."""
    lag_1 = series[i - 1]
    ma_3 = sum(series[max(0, i - 3):i]) / len(series[max(0, i - 3):i])
    ma_7 = sum(series[max(0, i - 7):i]) / len(series[max(0, i - 7):i])
    dow = (start_day + timedelta(days=i)).weekday()
    return [lag_1, ma_3, ma_7, float(dow)]


def walk_forward_ridge(series: list[float], start_day: date,
                       min_train: int = 7, alpha: float = 1.0
                       ) -> tuple[list[float], list[float]]:
    """Para cada día desde min_train: entrena Ridge con todos los días
    anteriores y predice el día actual. Devuelve (reales, predichos).
    Mismos periodos que el baseline para comparar de forma justa."""
    y_true: list[float] = []
    y_pred: list[float] = []
    for i in range(min_train, len(series)):
        # construir dataset de entrenamiento con días [min_train_feat, i)
        X_tr, y_tr = [], []
        for j in range(8, i):  # desde 8 para tener lag_7 completo
            X_tr.append(_features_at(series, j, start_day))
            y_tr.append(series[j])
        if len(X_tr) < 3:
            # muy pocos datos para entrenar: cae al último valor conocido
            y_pred.append(series[i - 1]); y_true.append(series[i]); continue
        model = Ridge(alpha=alpha)
        model.fit(np.array(X_tr), np.array(y_tr))
        x_i = np.array([_features_at(series, i, start_day)])
        y_pred.append(float(model.predict(x_i)[0]))
        y_true.append(series[i])
    return y_true, y_pred
