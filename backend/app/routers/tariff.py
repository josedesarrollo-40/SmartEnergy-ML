from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.tariff import TariffOut, TariffUpdate
from app.services.tariff_service import get_effective_tariff, set_tariff

router = APIRouter(prefix="/api/tariff", tags=["tariff"])


def _to_out(tariff) -> TariffOut:
    """Serializa una Tariff a TariffOut. Si no está guardada (id None), marca
    persisted=False para que el frontend sepa que es la por defecto."""
    return TariffOut(
        id=tariff.id,
        price_per_kwh=float(tariff.price_per_kwh),
        currency=tariff.currency,
        valid_from=tariff.valid_from,
        created_at=tariff.created_at,
        persisted=tariff.id is not None,
    )


@router.get("", response_model=TariffOut)
def read_tariff(db: Session = Depends(get_db)):
    """SOLO LECTURA. Devuelve la tarifa vigente o, si no hay ninguna, la tarifa
    por defecto del entorno SIN guardarla (persisted=False)."""
    return _to_out(get_effective_tariff(db))


@router.put("", response_model=TariffOut)
def update_tariff(payload: TariffUpdate, db: Session = Depends(get_db)):
    tariff = set_tariff(db, payload.price_per_kwh, payload.currency, payload.valid_from)
    return _to_out(tariff)
