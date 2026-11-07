"""Política de tarifas históricas: el costo de un tramo usa la tarifa vigente
en la FECHA INICIAL del tramo. Una tarifa que entra en vigencia dentro del
intervalo no afecta a ese intervalo; aplica a los siguientes cuya fecha inicial
sea >= su valid_from. Nunca se aplica una tarifa futura.

Usan una sesión SQLite real porque get_tariff_for_date consulta la base.
"""

import tempfile
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.tariff import Tariff
from app.services.consumption import cost_by_period, intervals_from_readings
from app.services.tariff_service import get_tariff_for_date, set_tariff


@pytest.fixture()
def db() -> Iterator:
    fd, path = tempfile.mkstemp(suffix=".db")
    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()
        import os
        os.close(fd)
        os.unlink(path)


def _price_for(db):
    """Igual que en analytics.summary: resuelve precio por fecha de inicio."""
    cache: dict[date, float] = {}

    def fn(on_date: date) -> float:
        if on_date not in cache:
            cache[on_date] = float(get_tariff_for_date(db, on_date).price_per_kwh)
        return cache[on_date]
    return fn


def _count(db) -> int:
    return db.execute(select(func.count()).select_from(Tariff)).scalar()


# --- Caso A: cambio de tarifa DENTRO del periodo -> no aplica al tramo -------

def test_caso_a_cambio_dentro_del_periodo(db):
    # Tarifa 1200 desde 2026-01-05. Tramo 2026-01-01 -> 2026-01-11 (50 kWh).
    # El tramo empieza el 01-01, antes de la vigencia: NO usa 1200.
    set_tariff(db, 1200.0, "COP", date(2026, 1, 5))
    intervals = intervals_from_readings([
        (date(2026, 1, 1), 100.0),
        (date(2026, 1, 11), 150.0),
    ])
    # Sin tarifa vigente el 01-01 -> tarifa por defecto 997.92.
    assert cost_by_period(intervals, _price_for(db)) == round(50 * 997.92, 2)


# --- Caso B: tarifa nueva vigente al inicio ---------------------------------

def test_caso_b_tarifa_vigente_al_inicio(db):
    # Tarifa 1200 desde 2026-01-05. Tramo 2026-01-11 -> 2026-01-21 (30 kWh).
    set_tariff(db, 1200.0, "COP", date(2026, 1, 5))
    intervals = intervals_from_readings([
        (date(2026, 1, 11), 150.0),
        (date(2026, 1, 21), 180.0),
    ])
    assert cost_by_period(intervals, _price_for(db)) == round(30 * 1200, 2)


# --- Caso C: vigencia EXACTAMENTE en la fecha inicial -----------------------

def test_caso_c_vigencia_exacta_en_fecha_inicial(db):
    # valid_from = fecha inicial del tramo -> se aplica (valid_from <= on_date).
    set_tariff(db, 1200.0, "COP", date(2026, 1, 5))
    t = get_tariff_for_date(db, date(2026, 1, 5))
    assert float(t.price_per_kwh) == 1200.0


# --- Caso D: sin tarifas guardadas -> default, sin escribir -----------------

def test_caso_d_sin_tarifas_usa_default_sin_escribir(db):
    assert _count(db) == 0
    t = get_tariff_for_date(db, date(2026, 1, 1))
    assert float(t.price_per_kwh) == 997.92
    assert t.id is None          # no persistida
    assert _count(db) == 0       # no insertó nada


# --- Caso E: varias tarifas historicas --------------------------------------

def test_caso_e_varias_tarifas_elige_la_vigente(db):
    set_tariff(db, 900.0, "COP", date(2026, 1, 1))
    set_tariff(db, 1000.0, "COP", date(2026, 2, 1))
    set_tariff(db, 1100.0, "COP", date(2026, 3, 1))

    # En 2026-02-15 la vigente es la de 02-01 (1000).
    assert float(get_tariff_for_date(db, date(2026, 2, 15)).price_per_kwh) == 1000.0
    # En 2026-01-10 la vigente es la de 01-01 (900).
    assert float(get_tariff_for_date(db, date(2026, 1, 10)).price_per_kwh) == 900.0
    # En 2026-03-01 (exacta) la de 03-01 (1100).
    assert float(get_tariff_for_date(db, date(2026, 3, 1)).price_per_kwh) == 1100.0


def test_caso_e_nunca_tarifa_futura(db):
    # Única tarifa con valid_from futuro respecto a la fecha consultada.
    set_tariff(db, 1200.0, "COP", date(2026, 6, 1))
    t = get_tariff_for_date(db, date(2026, 1, 1))  # antes de la vigencia
    # No debe usar la de 1200 (futura): cae a default.
    assert float(t.price_per_kwh) == 997.92
    assert t.id is None
