from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reading import MeterReading
from app.schemas.analytics import DataQualityOut, SummaryOut
from app.services.data_quality import build_quality_report
from app.services.consumption import (
    avg_daily_kwh,
    cost_by_period,
    estimate_cost,
    intervals_from_readings,
    monthly_projection,
    total_kwh,
)
from app.services.tariff_service import get_effective_tariff, get_tariff_for_date

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _ordered_readings(db: Session) -> list[MeterReading]:
    return list(
        db.execute(
            select(MeterReading).order_by(
                MeterReading.reading_date.asc(), MeterReading.reading_time.asc()
            )
        ).scalars().all()
    )


@router.get("/summary", response_model=SummaryOut)
def summary(db: Session = Depends(get_db)):
    """Resumen para el dashboard: consumo total, promedio diario, costo y
    proyección mensual. La proyección es estadística (promedio * 30), NO ML.

    El costo total cobra cada tramo con la tarifa vigente en su fecha (regla 7).
    """
    readings = _ordered_readings(db)
    current = get_effective_tariff(db)  # solo lectura, no crea tarifa

    pairs = [(r.reading_date, r.value_kwh) for r in readings]
    intervals = intervals_from_readings(pairs)

    kwh = total_kwh(intervals)
    avg = avg_daily_kwh(intervals)

    # Precio por fecha: cachea las tarifas ya consultadas.
    _cache: dict[date, float] = {}

    def price_for(on_date: date) -> float:
        if on_date not in _cache:
            _cache[on_date] = float(get_tariff_for_date(db, on_date).price_per_kwh)
        return _cache[on_date]

    cost = cost_by_period(intervals, price_for)

    proj_kwh = monthly_projection(avg)
    proj_cost = estimate_cost(proj_kwh, current.price_per_kwh)

    last = readings[-1] if readings else None
    return SummaryOut(
        last_reading_date=last.reading_date if last else None,
        last_reading_value=float(last.value_kwh) if last else None,
        total_kwh=round(kwh, 3),
        avg_daily_kwh=round(avg, 3),
        estimated_cost=cost,
        currency=current.currency,
        monthly_projection_kwh=proj_kwh,
        monthly_projection_cost=proj_cost,
    )


@router.get("/data-quality", response_model=DataQualityOut)
def data_quality(db: Session = Depends(get_db)):
    """Reporte de calidad del histórico: días observados vs estimados, fechas
    pendientes, intervalos irregulares. Solo lectura, no modifica nada."""
    readings = _ordered_readings(db)
    return build_quality_report(readings)
