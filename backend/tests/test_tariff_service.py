"""Pruebas del servicio de tarifas con una sesión SQLite propia. Cuentan filas
directamente para demostrar qué funciones escriben y cuáles no."""

import tempfile
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.tariff import Tariff
from app.services.tariff_service import (
    default_tariff_unsaved,
    ensure_default_tariff,
    get_current_tariff,
    get_effective_tariff,
    get_tariff_for_date,
    set_tariff,
)
from datetime import date


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


def _count(db) -> int:
    return db.execute(select(func.count()).select_from(Tariff)).scalar()


def test_get_current_tariff_vacio_no_escribe(db):
    assert get_current_tariff(db) is None
    assert _count(db) == 0


def test_get_effective_tariff_vacio_no_escribe(db):
    t = get_effective_tariff(db)
    assert t.id is None                 # objeto en memoria
    assert float(t.price_per_kwh) == 997.92
    assert _count(db) == 0              # NO creó fila


def test_get_tariff_for_date_vacio_no_escribe(db):
    t = get_tariff_for_date(db, date(2026, 1, 1))
    assert t.id is None
    assert _count(db) == 0


def test_default_tariff_unsaved_no_escribe(db):
    t = default_tariff_unsaved()
    assert t.id is None
    assert _count(db) == 0


def test_ensure_default_tariff_si_escribe(db):
    assert _count(db) == 0
    t = ensure_default_tariff(db)
    assert t.id is not None
    assert _count(db) == 1
    # Idempotente: segunda llamada no crea otra.
    ensure_default_tariff(db)
    assert _count(db) == 1


def test_set_tariff_escribe(db):
    set_tariff(db, 1000.0, "COP", None)
    assert _count(db) == 1
    assert float(get_current_tariff(db).price_per_kwh) == 1000.0
