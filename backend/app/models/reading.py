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

# Precisión de kWh: hasta 99999999.999 (3 decimales). Suficiente para un contador
# residencial. Numeric evita los errores de redondeo del float.
KWH_NUMERIC = Numeric(12, 3)


class MeterReading(Base):
    """Una lectura del contador eléctrico en una fecha dada.

    value_kwh es el número que marca el contador (acumulado, siempre sube).
    El consumo entre dos lecturas se calcula, no se guarda aquí.
    """

    __tablename__ = "meter_readings"
    __table_args__ = (
        UniqueConstraint("reading_date", name="uq_meter_readings_reading_date"),
        CheckConstraint("value_kwh >= 0", name="ck_meter_readings_value_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value_kwh: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    note: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DeletedReading(Base):
    """Auditoría: una lectura borrada se copia aquí antes de quitarla de
    meter_readings. Conserva el rastro de lo eliminado."""

    __tablename__ = "deleted_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_id: Mapped[int] = mapped_column(nullable=False)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_kwh: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    note: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
