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
