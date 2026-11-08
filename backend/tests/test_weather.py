"""Clima por intervalo: tolerancia a fallos, intervalo correcto, sin duplicados,
estados de disponibilidad y recuperación de pendientes.

Se usa un fetcher simulado (sin red) para controlar cada escenario.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.reading import MeterReading
from app.models.weather import (
    STATUS_AVAILABLE,
    STATUS_FAILED,
    STATUS_PENDING,
    IntervalWeather,
)
from app.services.weather_capture import (
    capture_for_interval,
    capture_latest_interval,
    recover_pending,
)
from app.services.weather_service import (
    WeatherAggregate,
    WeatherFetchError,
    WeatherUnavailable,
    aggregate_interval,
)
from app import models  # noqa: F401


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


def _add_reading(db, d, t, v):
    from datetime import date, time
    r = MeterReading(
        reading_date=date.fromisoformat(d),
        reading_time=time.fromisoformat(t),
        value_kwh=v,
        source="manual",
        date_confidence="verified",
        time_known=True,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# --- Agregación: límites temporales (sin doble conteo) --------------------

def test_aggregate_uses_half_open_interval():
    # Observaciones horarias; el intervalo (08:00, 10:00] toma 09:00 y 10:00,
    # NO 08:00 (frontera izquierda excluida para no contar dos veces).
    hourly = {
        "time": [
            "2026-01-01T08:00", "2026-01-01T09:00", "2026-01-01T10:00",
            "2026-01-01T11:00",
        ],
        "temperature_2m": [20.0, 22.0, 24.0, 26.0],
        "relative_humidity_2m": [50.0, 60.0, 70.0, 80.0],
    }
    agg = aggregate_interval(
        hourly, datetime(2026, 1, 1, 8, 0), datetime(2026, 1, 1, 10, 0)
    )
    assert agg.observation_count == 2            # 09:00 y 10:00
    assert agg.temp_avg_c == 23.0                # (22+24)/2
    assert agg.temp_max_c == 24.0 and agg.temp_min_c == 22.0
    assert agg.humidity_avg_pct == 65.0


def test_consecutive_intervals_do_not_double_count():
    hourly = {
        "time": ["2026-01-01T08:00", "2026-01-01T09:00", "2026-01-01T10:00"],
        "temperature_2m": [20.0, 22.0, 24.0],
        "relative_humidity_2m": [50.0, 60.0, 70.0],
    }
    a = aggregate_interval(hourly, datetime(2026, 1, 1, 8, 0), datetime(2026, 1, 1, 9, 0))
    b = aggregate_interval(hourly, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0))
    # 09:00 pertenece SOLO al primer intervalo; 10:00 solo al segundo.
    assert a.observation_count == 1 and b.observation_count == 1


def test_aggregate_no_observations_is_none_not_zero():
    hourly = {"time": [], "temperature_2m": [], "relative_humidity_2m": []}
    agg = aggregate_interval(hourly, datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 2, 0, 0))
    assert agg.observation_count == 0
    assert agg.temp_avg_c is None  # faltante NO se vuelve 0


# --- Captura con fetcher simulado -----------------------------------------

def test_capture_available(db):
    r1 = _add_reading(db, "2026-01-01", "08:00:00", 100)
    r2 = _add_reading(db, "2026-01-03", "08:00:00", 130)

    def fetcher(start_dt, end_dt):
        assert start_dt == datetime(2026, 1, 1, 8, 0)   # intervalo correcto
        assert end_dt == datetime(2026, 1, 3, 8, 0)
        return WeatherAggregate(23.5, 28.0, 19.0, 65.0, 48)

    row = capture_latest_interval(db, r2, fetcher=fetcher)
    db.commit()
    assert row.status == STATUS_AVAILABLE
    assert float(row.temp_avg_c) == 23.5
    assert row.observation_count == 48
    assert row.start_reading_id == r1.id and row.end_reading_id == r2.id


def test_capture_failure_marks_failed_not_raises(db):
    _add_reading(db, "2026-01-01", "08:00:00", 100)
    r2 = _add_reading(db, "2026-01-03", "08:00:00", 130)

    def fetcher(start_dt, end_dt):
        raise WeatherFetchError("timeout simulado")

    row = capture_latest_interval(db, r2, fetcher=fetcher)
    db.commit()
    assert row.status == STATUS_FAILED
    assert row.temp_avg_c is None  # nada inventado


def test_capture_recent_marks_pending(db):
    _add_reading(db, "2026-01-01", "08:00:00", 100)
    r2 = _add_reading(db, "2026-01-03", "08:00:00", 130)

    def fetcher(start_dt, end_dt):
        raise WeatherUnavailable("periodo muy reciente")

    row = capture_latest_interval(db, r2, fetcher=fetcher)
    db.commit()
    assert row.status == STATUS_PENDING


def test_no_previous_reading_no_interval(db):
    r1 = _add_reading(db, "2026-01-01", "08:00:00", 100)
    assert capture_latest_interval(db, r1, fetcher=lambda a, b: None) is None


def test_no_duplicate_interval_rows(db):
    _add_reading(db, "2026-01-01", "08:00:00", 100)
    r2 = _add_reading(db, "2026-01-03", "08:00:00", 130)

    def ok(start_dt, end_dt):
        return WeatherAggregate(20.0, 25.0, 15.0, 60.0, 10)

    capture_latest_interval(db, r2, fetcher=ok)
    db.commit()
    # Segunda captura del MISMO par actualiza, no duplica.
    capture_latest_interval(db, r2, fetcher=ok)
    db.commit()
    rows = db.execute(select(IntervalWeather)).scalars().all()
    assert len(rows) == 1


def test_recover_pending_updates(db):
    _add_reading(db, "2026-01-01", "08:00:00", 100)
    r2 = _add_reading(db, "2026-01-03", "08:00:00", 130)

    # Primero falla -> queda failed.
    capture_latest_interval(db, r2, fetcher=lambda a, b: (_ for _ in ()).throw(WeatherFetchError("x")))
    db.commit()

    # Luego recover con datos disponibles.
    def ok(start_dt, end_dt):
        return WeatherAggregate(21.0, 26.0, 16.0, 55.0, 48)

    result = recover_pending(db, fetcher=ok)
    db.commit()
    assert result["updated"] == 1
    row = db.execute(select(IntervalWeather)).scalars().first()
    assert row.status == STATUS_AVAILABLE


# --- Flujo completo por la API: la lectura se guarda aunque el clima falle --

def test_reading_still_created_when_weather_fails(client, monkeypatch):
    # Forzamos que la captura de clima lance: el POST de lectura debe seguir 201.
    import app.routers.readings as readings_mod

    def boom(db, reading, **kwargs):
        raise RuntimeError("fallo inesperado de clima")

    monkeypatch.setattr(readings_mod, "capture_latest_interval", boom)

    r = client.post(
        "/api/readings",
        json={"reading_date": "2026-01-05", "value_kwh": 200, "reading_time": "08:00:00"},
    )
    assert r.status_code == 201
    assert len(client.get("/api/readings").json()) == 1


def test_weather_intervals_endpoint_reports_unavailable(client, monkeypatch):
    # Evita cualquier llamada de red: la captura falla rápido (queda failed).
    import app.services.weather_capture as cap

    def no_network(start_dt, end_dt):
        raise WeatherFetchError("sin red en test")

    monkeypatch.setattr(cap, "_default_fetcher", no_network)

    client.post("/api/readings", json={"reading_date": "2026-01-01", "value_kwh": 100, "reading_time": "08:00:00"})
    client.post("/api/readings", json={"reading_date": "2026-01-03", "value_kwh": 130, "reading_time": "08:00:00"})
    rows = client.get("/api/weather/intervals").json()
    assert len(rows) == 1
    assert rows[0]["consumption_kwh"] == 30.0
    # Con captura fallida, el intervalo existe con estado failed y sin valores.
    assert rows[0]["status"] in ("failed", "pending")
    assert rows[0]["temp_avg_c"] is None
