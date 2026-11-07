import math
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingCreate(BaseModel):
    reading_date: date
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
    value_kwh: float
    note: str | None
    created_at: datetime
