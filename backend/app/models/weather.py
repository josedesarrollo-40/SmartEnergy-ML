from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Temperatura: -99.9..999.9 °C con 1 decimal (más que suficiente).
TEMP_NUMERIC = Numeric(5, 1)
# Humedad relativa 0..100 % con 1 decimal.
HUMIDITY_NUMERIC = Numeric(5, 1)

# Estados de captura del clima de un intervalo.
STATUS_PENDING = "pending"      # aún no consultado o periodo no disponible todavía
STATUS_AVAILABLE = "available"  # datos reales obtenidos y almacenados
STATUS_FAILED = "failed"        # la consulta falló (error/timeout); recuperable
VALID_STATUSES = (STATUS_PENDING, STATUS_AVAILABLE, STATUS_FAILED)


class IntervalWeather(Base):
    """Clima asociado al intervalo entre DOS lecturas consecutivas del contador.

    Dato INDEPENDIENTE de las lecturas eléctricas: no modifica meter_readings.
    El intervalo va de la lectura inicial (start) a la final (end). Las
    observaciones meteorológicas se agregan (promedio, máx, mín) sobre todo el
    periodo real entre ambas lecturas.

    Trazabilidad: `status` distingue pendiente / disponible / fallido, `source`
    identifica el proveedor y `fetched_at` la fecha de consulta. Los valores
    quedan en NULL mientras no haya datos reales: nunca se rellenan con ceros.
    """

    __tablename__ = "interval_weather"
    __table_args__ = (
        # Un intervalo (par de lecturas) tiene a lo sumo una fila de clima.
        UniqueConstraint(
            "start_reading_id", "end_reading_id", name="uq_interval_weather_pair"
        ),
        CheckConstraint(
            "status in ('pending', 'available', 'failed')",
            name="ck_interval_weather_status",
        ),
        CheckConstraint(
            "observation_count >= 0", name="ck_interval_weather_obs_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Lecturas que delimitan el intervalo. ON DELETE CASCADE: si se borra una de
    # las lecturas, el clima del intervalo deja de tener sentido.
    start_reading_id: Mapped[int] = mapped_column(
        ForeignKey("meter_readings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    end_reading_id: Mapped[int] = mapped_column(
        ForeignKey("meter_readings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Agregados del periodo. NULL mientras no haya datos reales (no 0).
    temp_avg_c: Mapped[Decimal | None] = mapped_column(TEMP_NUMERIC, nullable=True)
    temp_max_c: Mapped[Decimal | None] = mapped_column(TEMP_NUMERIC, nullable=True)
    temp_min_c: Mapped[Decimal | None] = mapped_column(TEMP_NUMERIC, nullable=True)
    humidity_avg_pct: Mapped[Decimal | None] = mapped_column(
        HUMIDITY_NUMERIC, nullable=True
    )
    # Cuántas observaciones horarias se usaron para los agregados.
    observation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # Proveedor de los datos (p. ej. 'open-meteo'). Trazabilidad de la fuente.
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # Fecha/hora de la última consulta realizada (éxito o fallo).
    fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
