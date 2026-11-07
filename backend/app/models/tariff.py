from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Precio por kWh: hasta 9999999.9999 (4 decimales). Numeric para no perder
# centavos por redondeo del float.
PRICE_NUMERIC = Numeric(11, 4)


class Tariff(Base):
    """Tarifa eléctrica por kWh. Se guarda historial: la vigente es la de
    valid_from más reciente."""

    __tablename__ = "tariffs"
    __table_args__ = (
        CheckConstraint("price_per_kwh > 0", name="ck_tariffs_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    price_per_kwh: Mapped[Decimal] = mapped_column(PRICE_NUMERIC, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="COP")
    valid_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
