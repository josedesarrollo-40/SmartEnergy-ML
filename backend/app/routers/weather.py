"""Endpoints de clima por intervalo.

- GET  /api/weather/intervals  : intervalos entre lecturas con su consumo
  eléctrico (calculado por el backend) y su clima + estado de disponibilidad.
- POST /api/weather/recover    : recupera intervalos pendientes/fallidos
  consultando Open-Meteo de nuevo. NO se dispara al cargar páginas.

La consulta a Open-Meteo ocurre solo en /recover (o al registrar una lectura),
nunca en el GET: cargar la analítica no debe disparar llamadas externas.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reading import MeterReading
from app.models.weather import IntervalWeather
from app.schemas.weather import IntervalWeatherRow, WeatherBackfillResult
from app.services.weather_capture import recover_pending

router = APIRouter(prefix="/api/weather", tags=["weather"])

# Atribución de la fuente de datos meteorológicos.
ATTRIBUTION = "Weather data by Open-Meteo.com (CC BY 4.0)"


@router.get("/intervals", response_model=list[IntervalWeatherRow])
def list_interval_weather(db: Session = Depends(get_db)):
    """Lista los intervalos entre lecturas consecutivas con su consumo y clima.

    El consumo lo calcula el backend (diferencia de acumulados). El clima viene
    de interval_weather; si un intervalo aún no tiene fila, su estado es
    'unavailable' y los valores van en null (sin inventar datos)."""
    readings = list(
        db.execute(
            select(MeterReading).order_by(
                MeterReading.reading_date.asc(), MeterReading.reading_time.asc()
            )
        ).scalars().all()
    )
    weather_by_pair = {
        (w.start_reading_id, w.end_reading_id): w
        for w in db.execute(select(IntervalWeather)).scalars().all()
    }

    rows: list[IntervalWeatherRow] = []
    for prev, cur in zip(readings, readings[1:]):
        consumption = (
            float(cur.value_kwh) - float(prev.value_kwh)
            if cur.value_kwh >= prev.value_kwh
            else None
        )
        w = weather_by_pair.get((prev.id, cur.id))
        if w is None:
            rows.append(
                IntervalWeatherRow(
                    start_reading_id=prev.id,
                    end_reading_id=cur.id,
                    start_date=prev.reading_date.isoformat(),
                    end_date=cur.reading_date.isoformat(),
                    consumption_kwh=consumption,
                    temp_avg_c=None,
                    temp_max_c=None,
                    temp_min_c=None,
                    humidity_avg_pct=None,
                    observation_count=0,
                    status="unavailable",
                    source=None,
                )
            )
            continue
        rows.append(
            IntervalWeatherRow(
                start_reading_id=prev.id,
                end_reading_id=cur.id,
                start_date=prev.reading_date.isoformat(),
                end_date=cur.reading_date.isoformat(),
                consumption_kwh=consumption,
                temp_avg_c=float(w.temp_avg_c) if w.temp_avg_c is not None else None,
                temp_max_c=float(w.temp_max_c) if w.temp_max_c is not None else None,
                temp_min_c=float(w.temp_min_c) if w.temp_min_c is not None else None,
                humidity_avg_pct=(
                    float(w.humidity_avg_pct)
                    if w.humidity_avg_pct is not None
                    else None
                ),
                observation_count=w.observation_count,
                status=w.status,
                source=w.source,
            )
        )
    return rows


@router.post("/recover", response_model=WeatherBackfillResult)
def recover(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=500),
):
    """Reintenta los intervalos pendientes/fallidos. Acción explícita del
    usuario; no se ejecuta al cargar páginas."""
    result = recover_pending(db, limit=limit)
    db.commit()
    return WeatherBackfillResult(**result)
