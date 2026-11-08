from datetime import date

from pydantic import BaseModel


class PeriodConsumption(BaseModel):
    start_date: date
    end_date: date
    days: int
    kwh: float
    avg_daily_kwh: float
    estimated_cost: float
    currency: str


class SummaryOut(BaseModel):
    last_reading_date: date | None
    last_reading_value: float | None
    total_kwh: float
    avg_daily_kwh: float
    estimated_cost: float
    currency: str
    monthly_projection_kwh: float
    monthly_projection_cost: float


class HistoryPoint(BaseModel):
    label: str          # día/semana/mes
    kwh: float


class PredictionPoint(BaseModel):
    target_date: date
    predicted_kwh: float


class PredictionOut(BaseModel):
    method: str         # "statistical" o "ml"
    confidence_note: str
    points: list[PredictionPoint]


class PeriodConsumptionOut(BaseModel):
    start: date
    end: date
    kwh: float
    estimated: bool            # hubo interpolación en bordes
    estimated_fraction: float  # proporción del kWh estimada
    sufficient: bool           # False si no hay datos suficientes
    estimated_cost: float
    currency: str
    note: str


class InvoiceComparisonOut(BaseModel):
    period_start: date
    period_end: date
    # calculado por SmartEnergy ML
    calculated_kwh: float
    calculated_cost: float
    calculated_sufficient: bool
    calculated_estimated: bool
    # facturado
    billed_kwh: float
    billed_amount: float
    # diferencias (calculado - facturado)
    kwh_diff: float
    kwh_diff_pct: float | None       # None si billed_kwh = 0
    cost_diff: float
    cost_diff_pct: float | None      # None si billed_amount = 0
    currency: str
    note: str


class DataQualityOut(BaseModel):
    total_readings: int
    first_date: date | None
    last_date: date | None
    span_days: int
    observed_days: int
    interpolated_days: int
    missing_days: int
    time_known_count: int
    confidence_counts: dict[str, int]
    source_counts: dict[str, int]
    irregular_intervals: list[dict]
    pending_or_inferred: int
