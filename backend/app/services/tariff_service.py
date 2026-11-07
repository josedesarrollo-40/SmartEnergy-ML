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
    """SOLO LECTURA. Tarifa vigente en una fecha dada.

    Regla de tarifas históricas:
    1. Busca tarifas con valid_from <= on_date.
    2. Ordena por valid_from DESC (desempata por id DESC).
    3. Devuelve la más reciente de esas.
    4. Si NINGUNA tarifa tiene vigencia en o antes de on_date, usa la tarifa por
       defecto en memoria (default_tariff_unsaved). NUNCA usa una tarifa cuya
       valid_from sea posterior a on_date (no se aplica una tarifa futura a un
       periodo anterior a su entrada en vigencia).
    Nunca escribe en la base.
    """
    stmt = (
        select(Tariff)
        .where(Tariff.valid_from <= on_date)
        .order_by(Tariff.valid_from.desc(), Tariff.id.desc())
    )
    tariff = db.execute(stmt).scalars().first()
    if tariff is not None:
        return tariff

    # Ninguna tarifa vigente en o antes de on_date: tarifa por defecto en
    # memoria. No se usa una tarifa futura ni se persiste nada.
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
