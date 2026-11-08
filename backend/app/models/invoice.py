from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

KWH_NUMERIC = Numeric(12, 3)
MONEY_NUMERIC = Numeric(14, 2)


class Invoice(Base):
    """Factura real del comercializador. Dato INDEPENDIENTE de las lecturas:
    nunca reemplaza ni modifica meter_readings. Se usa para comparar el consumo
    y costo calculados por SmartEnergy ML contra lo facturado."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("period_start", "period_end", name="uq_invoices_period"),
        CheckConstraint("period_end >= period_start", name="ck_invoices_period_order"),
        CheckConstraint("billed_kwh >= 0", name="ck_invoices_kwh_non_negative"),
        CheckConstraint("billed_amount >= 0", name="ck_invoices_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    billed_kwh: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    billed_amount: Mapped[Decimal] = mapped_column(MONEY_NUMERIC, nullable=False)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
