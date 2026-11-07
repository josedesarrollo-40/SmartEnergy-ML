import math
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TariffUpdate(BaseModel):
    price_per_kwh: float = Field(gt=0)
    currency: str = "COP"
    valid_from: date | None = None

    @field_validator("price_per_kwh")
    @classmethod
    def price_must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price_per_kwh debe ser un número finito.")
        return v


class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    price_per_kwh: float
    currency: str
    valid_from: date
    created_at: datetime
