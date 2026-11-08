"""Pruebas del módulo ML: clasificación de días, separación observado/
interpolado y validación temporal sin fuga de información."""

from datetime import datetime, time

from app.ml.dataset import Reading, build_daily_series, classify_counts
from app.ml.baseline import moving_average_forecast, walk_forward_baseline
from app.ml.evaluate import mae, metrics, metrics_masked


def _r(d, v, prov="verificada", ht=True):
    return Reading(dt=datetime.combine(d, time(8, 0) if ht else time(0, 0)),
                   value_kwh=v, provenance=prov, has_real_time=ht)


def test_classify_counts():
    from datetime import date
    rs = [_r(date(2026, 1, 1), 100, "verificada", True),
          _r(date(2026, 1, 2), 110, "pendiente", False),
          _r(date(2026, 1, 3), 120, "inferida", False)]
    c = classify_counts(rs)
    assert c["_total"] == 3
    assert c["_con_hora_real"] == 1
    assert c["verificada"] == 1 and c["pendiente"] == 1 and c["inferida"] == 1


def test_daily_series_marks_observed_and_interpolated():
    from datetime import date
    # Intervalo de 1 dia -> 1 observado. Intervalo de 3 dias -> 2 interp + 1 obs.
    rs = [_r(date(2026, 1, 1), 100),
          _r(date(2026, 1, 2), 110),           # +10 en 1 dia -> observado
          _r(date(2026, 1, 5), 140)]           # +30 en 3 dias -> 10/dia
    daily = build_daily_series(rs)
    kinds = [(p.day.isoformat(), p.kind, p.kwh) for p in daily]
    # dia 02: observado 10; dias 03,04 interpolados 10; dia 05 observado 10
    assert kinds[0] == ("2026-01-02", "observado", 10.0)
    assert kinds[1][1] == "interpolado"
    assert kinds[2][1] == "interpolado"
    assert kinds[3][1] == "observado"


def test_daily_series_skips_decreasing():
    from datetime import date
    rs = [_r(date(2026, 1, 1), 100), _r(date(2026, 1, 2), 90)]  # baja
    assert build_daily_series(rs) == []


def test_moving_average_uses_only_past():
    # La media movil solo mira la historia pasada que se le entrega.
    assert moving_average_forecast([2, 4, 6], window=3) == 4.0
    assert moving_average_forecast([10], window=7) == 10.0


def test_walk_forward_no_future_leak():
    # Cada prediccion del baseline en i usa solo series[:i].
    series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    y_true, y_pred = walk_forward_baseline(series, window=3, min_train=3)
    # primera prediccion (i=3) = media de [1,2,3] = 2.0 ; real = 4
    assert y_pred[0] == 2.0
    assert y_true[0] == 4
    # longitud = len - min_train
    assert len(y_true) == len(series) - 3


def test_metrics_masked_filters_to_observed():
    yt = [10, 20, 30, 40]
    yp = [12, 25, 33, 38]
    keep = [True, False, True, False]  # solo dias 0 y 2
    m = metrics_masked(yt, yp, keep)
    assert m["n"] == 2
    # MAE de (|10-12|, |30-33|) = (2+3)/2 = 2.5
    assert m["MAE"] == 2.5


def test_metrics_empty_is_safe():
    m = metrics([], [])
    assert m["n"] == 0 and m["MAE"] is None
