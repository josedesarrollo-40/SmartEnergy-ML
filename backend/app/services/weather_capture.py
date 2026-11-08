"""Captura y persistencia del clima por intervalo de lecturas.

Orquesta: dada una lectura recién creada, identifica la lectura anterior, define
el intervalo real (par ordenado de lecturas) y guarda/actualiza su clima en
interval_weather, respetando estados y sin duplicar (UNIQUE del par).

Separado del router para poder probarlo sin FastAPI y sin red (inyectando un
fetcher simulado).
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reading import MeterReading
from app.models.weather import (
    STATUS_AVAILABLE,
    STATUS_FAILED,
    STATUS_PENDING,
    IntervalWeather,
)
from app.services.weather_service import (
    SOURCE,
    WeatherAggregate,
    WeatherFetchError,
    WeatherUnavailable,
    as_decimal,
    compute_interval_weather,
)

# Un fetcher recibe (start_dt, end_dt) y devuelve un WeatherAggregate, o lanza
# WeatherUnavailable / WeatherFetchError. Por defecto consulta Open-Meteo.
Fetcher = Callable[[datetime, datetime], WeatherAggregate]


def _default_fetcher(start_dt: datetime, end_dt: datetime) -> WeatherAggregate:
    return compute_interval_weather(start_dt, end_dt)


def _previous_reading(db: Session, reading: MeterReading) -> MeterReading | None:
    """Lectura inmediatamente anterior a `reading` en orden (fecha, hora)."""
    stmt = (
        select(MeterReading)
        .where(
            (MeterReading.reading_date < reading.reading_date)
            | (
                (MeterReading.reading_date == reading.reading_date)
                & (MeterReading.reading_time < reading.reading_time)
            )
        )
        .order_by(
            MeterReading.reading_date.desc(), MeterReading.reading_time.desc()
        )
    )
    return db.execute(stmt).scalars().first()


def _apply_aggregate(
    row: IntervalWeather, agg: WeatherAggregate, status: str
) -> None:
    row.temp_avg_c = as_decimal(agg.temp_avg_c)
    row.temp_max_c = as_decimal(agg.temp_max_c)
    row.temp_min_c = as_decimal(agg.temp_min_c)
    row.humidity_avg_pct = as_decimal(agg.humidity_avg_pct)
    row.observation_count = agg.observation_count
    row.status = status
    row.source = SOURCE
    row.fetched_at = datetime.now()


def _get_or_create_row(
    db: Session, start: MeterReading, end: MeterReading
) -> IntervalWeather:
    existing = db.execute(
        select(IntervalWeather).where(
            IntervalWeather.start_reading_id == start.id,
            IntervalWeather.end_reading_id == end.id,
        )
    ).scalars().first()
    if existing is not None:
        return existing
    row = IntervalWeather(
        start_reading_id=start.id,
        end_reading_id=end.id,
        status=STATUS_PENDING,
        source=SOURCE,
        observation_count=0,
    )
    db.add(row)
    return row


def capture_for_interval(
    db: Session,
    start: MeterReading,
    end: MeterReading,
    *,
    fetcher: Fetcher | None = None,
) -> IntervalWeather:
    """Captura (o actualiza) el clima del intervalo (start, end].

    Nunca lanza: traduce los fallos a estado persistido (pending/failed). Así el
    registro de la lectura nunca se ve afectado por un error de Open-Meteo.
    """
    fetch = fetcher or _default_fetcher
    row = _get_or_create_row(db, start, end)

    start_dt = datetime.combine(start.reading_date, start.reading_time)
    end_dt = datetime.combine(end.reading_date, end.reading_time)

    try:
        agg = fetch(start_dt, end_dt)
    except WeatherUnavailable:
        # Periodo demasiado reciente: pendiente para recuperación futura.
        row.status = STATUS_PENDING
        row.source = SOURCE
        row.fetched_at = datetime.now()
        return row
    except WeatherFetchError:
        row.status = STATUS_FAILED
        row.source = SOURCE
        row.fetched_at = datetime.now()
        return row

    if agg.observation_count == 0:
        # Sin observaciones utilizables: no se inventan ceros; queda pendiente.
        row.status = STATUS_PENDING
        row.source = SOURCE
        row.fetched_at = datetime.now()
        return row

    _apply_aggregate(row, agg, STATUS_AVAILABLE)
    return row


def capture_latest_interval(
    db: Session, reading: MeterReading, *, fetcher: Fetcher | None = None
) -> IntervalWeather | None:
    """Tras registrar `reading`, captura el clima del intervalo formado por su
    lectura anterior y ella. Devuelve la fila de clima, o None si no hay lectura
    anterior (no hay intervalo todavía).

    Best-effort: no propaga excepciones; el commit lo hace el llamador.
    """
    prev = _previous_reading(db, reading)
    if prev is None:
        return None
    return capture_for_interval(db, prev, reading, fetcher=fetcher)


def recover_pending(
    db: Session, *, fetcher: Fetcher | None = None, limit: int | None = None
) -> dict[str, int]:
    """Reintenta los intervalos en estado pending/failed. Devuelve un conteo.

    No crea intervalos nuevos: solo recupera los ya registrados. Evita consultas
    repetidas innecesarias al no tocar los que ya están 'available'.
    """
    stmt = (
        select(IntervalWeather)
        .where(IntervalWeather.status.in_([STATUS_PENDING, STATUS_FAILED]))
        .order_by(IntervalWeather.id.asc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = list(db.execute(stmt).scalars().all())

    checked = updated = still_pending = failed = 0
    for row in rows:
        start = db.get(MeterReading, row.start_reading_id)
        end = db.get(MeterReading, row.end_reading_id)
        checked += 1
        if start is None or end is None:
            continue
        before = row.status
        capture_for_interval(db, start, end, fetcher=fetcher)
        if row.status == STATUS_AVAILABLE:
            updated += 1
        elif row.status == STATUS_FAILED:
            failed += 1
        else:
            still_pending += 1
        _ = before
    return {
        "checked": checked,
        "updated": updated,
        "still_pending": still_pending,
        "failed": failed,
    }
