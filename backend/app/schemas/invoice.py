import math
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InvoiceCreate(BaseModel):
    period_start: date
    period_end: date
    billed_kwh: float = Field(ge=0)
    billed_amount: float = Field(ge=0)
    issued_date: date | None = None
    notes: str | None = None

    @field_validator("billed_kwh", "billed_amount")
    @classmethod
    def finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("El valor debe ser finito.")
        return v

    @model_validator(mode="after")
    def period_ok(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end no puede ser anterior a period_start.")
        return self


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period_start: date
    period_end: date
    billed_kwh: float
    billed_amount: float
    issued_date: date | None
    notes: str | None
    created_at: datetime
