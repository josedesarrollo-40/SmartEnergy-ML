from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reading import MeterReading
import calendar

from fastapi import HTTPException, Query, status

from app.schemas.analytics import (
    DataQualityOut,
    PeriodConsumptionOut,
    SummaryOut,
)
from app.services.consumption import consumption_between, cost_between
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


def _period_result(db: Session, start: date, end: date) -> PeriodConsumptionOut:
    """Calcula consumo y costo de un rango [start,end] con tarifas históricas.
    No modifica el cálculo de summary; es una función aparte."""
    readings = _ordered_readings(db)
    current = get_effective_tariff(db)
    pairs = [(r.reading_date, r.value_kwh) for r in readings]
    period = consumption_between(pairs, start, end)

    intervals = intervals_from_readings(pairs)
    _cache: dict[date, float] = {}

    def price_for(on_date: date) -> float:
        if on_date not in _cache:
            _cache[on_date] = float(get_tariff_for_date(db, on_date).price_per_kwh)
        return _cache[on_date]

    cost = cost_between(period, intervals, price_for) if period.sufficient else 0.0
    return PeriodConsumptionOut(
        start=period.start, end=period.end, kwh=period.kwh,
        estimated=period.estimated, estimated_fraction=period.estimated_fraction,
        sufficient=period.sufficient, estimated_cost=cost,
        currency=current.currency, note=period.note,
    )


@router.get("/period", response_model=PeriodConsumptionOut)
def period_consumption(
    db: Session = Depends(get_db),
    start: date = Query(...),
    end: date = Query(...),
):
    """Consumo y costo de un rango arbitrario [start, end]."""
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'start' no puede ser posterior a 'end'.",
        )
    return _period_result(db, start, end)


@router.get("/monthly", response_model=PeriodConsumptionOut)
def monthly_consumption(
    db: Session = Depends(get_db),
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
):
    """Consumo y costo del mes calendario (día 1 al último día del mes)."""
    last_day = calendar.monthrange(year, month)[1]
    return _period_result(db, date(year, month, 1), date(year, month, last_day))
