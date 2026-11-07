from datetime import date

from app.services.consumption import (
    avg_daily_kwh,
    cost_by_period,
    estimate_cost,
    intervals_from_readings,
    monthly_projection,
    total_kwh,
)
from app.services.validation import ReadingValidationError, validate_new_reading


def test_intervals_basic():
    readings = [
        (date(2026, 1, 1), 100.0),
        (date(2026, 1, 11), 150.0),   # +50 kWh en 10 días
        (date(2026, 1, 21), 170.0),   # +20 kWh en 10 días
    ]
    intervals = intervals_from_readings(readings)
    assert len(intervals) == 2
    assert intervals[0].kwh == 50.0
    assert intervals[0].days == 10
    assert total_kwh(intervals) == 70.0
    assert avg_daily_kwh(intervals) == 3.5   # 70 kWh / 20 días


def test_intervals_skip_incoherent():
    # Valor que baja -> tramo incoherente, se omite.
    readings = [
        (date(2026, 1, 1), 100.0),
        (date(2026, 1, 11), 90.0),
    ]
    assert intervals_from_readings(readings) == []


def test_estimate_cost():
    assert estimate_cost(10, 997.92) == 9979.2


def test_monthly_projection():
    assert monthly_projection(3.5) == 105.0


def test_validation_counter_only_goes_up():
    try:
        validate_new_reading(date(2026, 1, 11), 90.0, date(2026, 1, 1), 100.0)
        assert False, "debió fallar: el valor baja"
    except ReadingValidationError:
        pass


def test_validation_date_must_advance():
    try:
        validate_new_reading(date(2026, 1, 1), 110.0, date(2026, 1, 1), 100.0)
        assert False, "debió fallar: la fecha no avanza"
    except ReadingValidationError:
        pass


def test_validation_first_reading_ok():
    # Primera lectura, sin anterior: no lanza.
    validate_new_reading(date(2026, 1, 1), 100.0, None, None)


def test_validation_negative_value():
    try:
        validate_new_reading(date(2026, 1, 1), -1.0, None, None)
        assert False, "debió fallar: valor negativo"
    except ReadingValidationError:
        pass


def test_validation_non_finite_value():
    try:
        validate_new_reading(date(2026, 1, 1), float("inf"), None, None)
        assert False, "debió fallar: valor no finito"
    except ReadingValidationError:
        pass


def test_estimate_cost_rounding():
    # Redondeo correcto a 2 decimales (ROUND_HALF_UP).
    assert estimate_cost(1, 0.005) == 0.01


def test_cost_by_period_historical_tariff():
    # Dos tramos con tarifas distintas según la fecha de inicio.
    readings = [
        (date(2026, 1, 1), 0.0),
        (date(2026, 1, 11), 100.0),   # tramo A: 100 kWh, empieza 2026-01-01
        (date(2026, 1, 21), 150.0),   # tramo B: 50 kWh, empieza 2026-01-11
    ]
    intervals = intervals_from_readings(readings)

    def price_for(d):
        return 1000.0 if d < date(2026, 1, 11) else 1200.0

    # 100 * 1000 + 50 * 1200 = 100000 + 60000 = 160000
    assert cost_by_period(intervals, price_for) == 160000.0


def test_cost_by_period_single_tariff():
    readings = [
        (date(2026, 1, 1), 0.0),
        (date(2026, 1, 11), 50.0),
    ]
    intervals = intervals_from_readings(readings)
    assert cost_by_period(intervals, lambda d: 997.92) == round(50 * 997.92, 2)
