"""Dataset ML con clima: mapeo intervalo->día, features sin imputar ceros y
comparación de tres vías en las mismas muestras."""

from datetime import date

from app.ml.weather_features import (
    DayWeather,
    compare_three_way,
    weather_by_day,
)


def test_weather_by_day_maps_interval_days():
    intervals = [
        {
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 1, 4),
            "temp_avg_c": 22.0,
            "temp_max_c": 28.0,
            "temp_min_c": 16.0,
            "humidity_avg_pct": 60.0,
        }
    ]
    by_day = weather_by_day(intervals)
    # Atribuye a los días 02, 03, 04 (posteriores al inicio, hasta el fin).
    assert set(by_day.keys()) == {date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)}
    assert by_day[date(2026, 1, 2)].temp_avg_c == 22.0


def test_weather_by_day_skips_intervals_without_data():
    intervals = [
        {"start_date": date(2026, 1, 1), "end_date": date(2026, 1, 3), "temp_avg_c": None,
         "temp_max_c": None, "temp_min_c": None, "humidity_avg_pct": None},
    ]
    assert weather_by_day(intervals) == {}  # sin datos: no se atribuye nada


def test_compare_three_way_same_samples():
    # Serie sintética de 30 días con clima completo.
    series = [10 + (i % 5) for i in range(30)]
    start = date(2026, 1, 1)
    from datetime import timedelta
    day_weather = {
        start + timedelta(days=i): DayWeather(22.0, 28.0, 16.0, 60.0)
        for i in range(31)
    }
    result = compare_three_way(series, start, day_weather, min_train=7)
    # Las tres vías evalúan el MISMO número de muestras (días con clima).
    n = result["samples_with_weather"]
    assert n > 0
    assert result["baseline"]["n"] == n
    assert result["ridge_no_weather"]["n"] == n
    assert result["ridge_with_weather"]["n"] == n


def test_compare_three_way_without_weather_has_zero_samples():
    series = [10 + (i % 5) for i in range(20)]
    start = date(2026, 1, 1)
    # Sin clima: la muestra común con clima es 0; no se declara nada apto.
    result = compare_three_way(series, start, {}, min_train=7)
    assert result["samples_with_weather"] == 0
    assert result["ridge_with_weather"]["n"] == 0
