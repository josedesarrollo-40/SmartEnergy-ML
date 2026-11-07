"""Acceso a la tarifa vigente.

Regla: NINGUNA función que usen los endpoints GET escribe en la base. La tarifa
por defecto se siembra con una operación explícita (`ensure_default_tariff`),
no dentro de una lectura.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.tariff import Tariff


def get_current_tariff(db: Session) -> Tariff | None:
    """SOLO LECTURA. Tarifa vigente (valid_from más reciente) o None si no hay
    ninguna. No crea nada."""
    stmt = select(Tariff).order_by(Tariff.valid_from.desc(), Tariff.id.desc())
    return db.execute(stmt).scalars().first()


def default_tariff_unsaved() -> Tariff:
    """Objeto Tariff EN MEMORIA con los valores del entorno. No se añade a la
    sesión ni se guarda: sirve para que los GET respondan una tarifa por defecto
    sin tocar la base. id queda en None (no persistida)."""
    s = get_settings()
    return Tariff(
        price_per_kwh=Decimal(str(s.default_price_per_kwh)),
        currency=s.default_currency,
        valid_from=date.today(),
    )


def get_effective_tariff(db: Session) -> Tariff:
    """SOLO LECTURA. La tarifa vigente si existe; si no, la por defecto en
    memoria (sin guardar). Nunca escribe."""
    return get_current_tariff(db) or default_tariff_unsaved()


def get_tariff_for_date(db: Session, on_date: date) -> Tariff:
    """SOLO LECTURA. Tarifa vigente en una fecha dada: la de valid_from más
    reciente que sea <= on_date. Si ninguna empieza antes de esa fecha, usa la
    más antigua que exista; si la base está vacía, la por defecto en memoria.
    Nunca escribe. Base de la regla 7 (costo por tarifa histórica)."""
    stmt = (
        select(Tariff)
        .where(Tariff.valid_from <= on_date)
        .order_by(Tariff.valid_from.desc(), Tariff.id.desc())
    )
    tariff = db.execute(stmt).scalars().first()
    if tariff is not None:
        return tariff

    oldest = db.execute(
        select(Tariff).order_by(Tariff.valid_from.asc(), Tariff.id.asc())
    ).scalars().first()
    if oldest is not None:
        return oldest

    # Base vacía: tarifa por defecto en memoria, sin guardar.
    return default_tariff_unsaved()


def ensure_default_tariff(db: Session) -> Tariff:
    """LA ÚNICA función de lectura/escritura. Si no hay ninguna tarifa, crea la
    por defecto y la guarda. Se llama en una operación explícita (seed), NUNCA
    desde un GET. Idempotente: si ya hay tarifa, no crea otra."""
    existing = get_current_tariff(db)
    if existing is not None:
        return existing
    tariff = default_tariff_unsaved()
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff


def set_tariff(
    db: Session, price_per_kwh: float, currency: str, valid_from: date | None
) -> Tariff:
    """Crea una tarifa nueva (lo usa PUT /api/tariff). Sí escribe, a propósito."""
    tariff = Tariff(
        price_per_kwh=Decimal(str(price_per_kwh)),
        currency=currency,
        valid_from=valid_from or date.today(),
    )
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff
