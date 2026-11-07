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

    # id y created_at son None cuando la tarifa es la por defecto en memoria
    # (todavía no hay ninguna guardada). persisted lo deja explícito para el
    # frontend.
    id: int | None = None
    price_per_kwh: float
    currency: str
    valid_from: date
    created_at: datetime | None = None
    persisted: bool = True
