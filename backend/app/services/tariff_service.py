"""Acceso a la tarifa vigente. Si no hay ninguna, usa la del .env."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.tariff import Tariff


def get_current_tariff(db: Session) -> Tariff:
    """Devuelve la tarifa vigente (valid_from más reciente). Si no existe
    ninguna fila, crea una con el valor por defecto del entorno."""
    stmt = select(Tariff).order_by(Tariff.valid_from.desc(), Tariff.id.desc())
    tariff = db.execute(stmt).scalars().first()
    if tariff is not None:
        return tariff

    settings = get_settings()
    tariff = Tariff(
        price_per_kwh=Decimal(str(settings.default_price_per_kwh)),
        currency=settings.default_currency,
        valid_from=date.today(),
    )
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff


def get_tariff_for_date(db: Session, on_date: date) -> Tariff:
    """Tarifa vigente en una fecha dada: la de valid_from más reciente que sea
    <= on_date. Si ninguna empieza antes de esa fecha, usa la más antigua que
    exista (o la actual/por defecto si no hay ninguna).

    Base de la regla 7: cada tramo de consumo se cobra con la tarifa de su
    periodo. Hoy, sin historial, todas las fechas caen en la misma tarifa.
    """
    stmt = (
        select(Tariff)
        .where(Tariff.valid_from <= on_date)
        .order_by(Tariff.valid_from.desc(), Tariff.id.desc())
    )
    tariff = db.execute(stmt).scalars().first()
    if tariff is not None:
        return tariff

    # No hay tarifa que empiece antes de esa fecha: usa la más antigua.
    oldest = db.execute(
        select(Tariff).order_by(Tariff.valid_from.asc(), Tariff.id.asc())
    ).scalars().first()
    if oldest is not None:
        return oldest

    # Base vacía: crea la tarifa por defecto.
    return get_current_tariff(db)


def set_tariff(
    db: Session, price_per_kwh: float, currency: str, valid_from: date | None
) -> Tariff:
    tariff = Tariff(
        price_per_kwh=Decimal(str(price_per_kwh)),
        currency=currency,
        valid_from=valid_from or date.today(),
    )
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff
