from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.tariff import TariffOut, TariffUpdate
from app.services.tariff_service import get_current_tariff, set_tariff

router = APIRouter(prefix="/api/tariff", tags=["tariff"])


@router.get("", response_model=TariffOut)
def read_tariff(db: Session = Depends(get_db)):
    return get_current_tariff(db)


@router.put("", response_model=TariffOut)
def update_tariff(payload: TariffUpdate, db: Session = Depends(get_db)):
    return set_tariff(db, payload.price_per_kwh, payload.currency, payload.valid_from)
