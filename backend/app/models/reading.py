from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Precisión de kWh: hasta 99999999.999 (3 decimales). Suficiente para un contador
# residencial. Numeric evita los errores de redondeo del float.
KWH_NUMERIC = Numeric(12, 3)

# Hora por defecto para lecturas sin hora (medianoche).
MIDNIGHT = time(0, 0, 0)


class MeterReading(Base):
    """Una lectura del contador eléctrico en una fecha y hora dadas.

    value_kwh es el número que marca el contador (acumulado, siempre sube).
    Se permiten varias lecturas el mismo día si tienen horas distintas.
    El consumo entre dos lecturas se calcula, no se guarda aquí.
    """

    __tablename__ = "meter_readings"
    __table_args__ = (
        # Permite varias lecturas por día: la unicidad es (fecha, hora).
        UniqueConstraint(
            "reading_date", "reading_time", name="uq_meter_readings_date_time"
        ),
        CheckConstraint("value_kwh >= 0", name="ck_meter_readings_value_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # Hora de la lectura. Por defecto medianoche, para compatibilidad con las
    # lecturas antiguas que solo tenían fecha.
    reading_time: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'00:00:00'")
    )
    value_kwh: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    note: Mapped[str | None] = mapped_column(nullable=True)
    # Procedencia y calidad del dato. Defaults compatibles con el histórico:
    # las lecturas existentes quedan como import / pending / hora desconocida.
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'import'")
    )  # manual | import | api
    date_confidence: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )  # verified | confirmed | inferred | pending
    time_known: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
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
    reading_time: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'00:00:00'")
    )
    value_kwh: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    note: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ReadingCorrection(Base):
    """Auditoría de correcciones de valor de una lectura. Cada cambio del
    value_kwh de una lectura existente deja aquí el rastro (valor anterior,
    nuevo, motivo). El cambio y este registro se hacen en una misma
    transacción: no hay correcciones silenciosas."""

    __tablename__ = "reading_corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_id: Mapped[int] = mapped_column(nullable=False, index=True)
    old_value: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    new_value: Mapped[Decimal] = mapped_column(KWH_NUMERIC, nullable=False)
    reason: Mapped[str | None] = mapped_column(nullable=True)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
