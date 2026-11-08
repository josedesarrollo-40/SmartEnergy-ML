from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IntervalWeatherOut(BaseModel):
    """Clima de un intervalo entre dos lecturas, tal como se almacena."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    start_reading_id: int
    end_reading_id: int
    temp_avg_c: float | None
    temp_max_c: float | None
    temp_min_c: float | None
    humidity_avg_pct: float | None
    observation_count: int
    status: str  # pending | available | failed
    source: str
    fetched_at: datetime | None
    created_at: datetime


class IntervalWeatherRow(BaseModel):
    """Fila para la analítica: el intervalo (fechas + consumo eléctrico) junto
    con su clima y el estado de disponibilidad. El consumo lo calcula el backend
    a partir de las lecturas; el frontend no lo recalcula."""

    start_reading_id: int
    end_reading_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str
    consumption_kwh: float | None
    temp_avg_c: float | None
    temp_max_c: float | None
    temp_min_c: float | None
    humidity_avg_pct: float | None
    observation_count: int
    status: str  # pending | available | failed | unavailable
    source: str | None


class WeatherBackfillResult(BaseModel):
    """Resultado de recuperar intervalos pendientes/fallidos."""

    checked: int
    updated: int
    still_pending: int
    failed: int
