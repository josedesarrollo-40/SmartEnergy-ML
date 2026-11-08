import math
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingCreate(BaseModel):
    reading_date: date
    # Hora opcional. Si no se envía, se asume medianoche (00:00).
    reading_time: time | None = None
    value_kwh: float = Field(ge=0, description="Valor acumulado que marca el contador")
    note: str | None = None

    @field_validator("value_kwh")
    @classmethod
    def value_must_be_finite(cls, v: float) -> float:
        # ge=0 ya rechaza negativos, pero NaN e infinito pasan ese filtro.
        if not math.isfinite(v):
            raise ValueError("value_kwh debe ser un número finito (no NaN ni infinito).")
        return v


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reading_date: date
    reading_time: time
    value_kwh: float
    note: str | None
    source: str
    date_confidence: str
    time_known: bool
    created_at: datetime


class ReadingCorrectionIn(BaseModel):
    new_value: float = Field(ge=0)
    reason: str | None = None

    @field_validator("new_value")
    @classmethod
    def finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("new_value debe ser finito.")
        return v
