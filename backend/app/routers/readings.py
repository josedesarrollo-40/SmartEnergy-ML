from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from decimal import Decimal

from app.db.session import get_db
from app.models.reading import (
    MIDNIGHT,
    DeletedReading,
    MeterReading,
    ReadingCorrection,
)
from app.schemas.reading import ReadingCorrectionIn, ReadingCreate, ReadingOut
from app.services.validation import ReadingValidationError, validate_new_reading
from app.services.weather_capture import capture_latest_interval

router = APIRouter(prefix="/api/readings", tags=["readings"])


@router.post("", response_model=ReadingOut, status_code=status.HTTP_201_CREATED)
def create_reading(payload: ReadingCreate, db: Session = Depends(get_db)):
    """Registra una lectura. Valida contra la última registrada por fecha+hora.

    Se permiten varias lecturas el mismo día con horas distintas. La UNIQUE
    (reading_date, reading_time) protege contra duplicados exactos y contra dos
    POST simultáneos que pasen la validación a la vez."""
    reading_time = payload.reading_time or MIDNIGHT

    last = db.execute(
        select(MeterReading).order_by(
            MeterReading.reading_date.desc(), MeterReading.reading_time.desc()
        )
    ).scalars().first()

    try:
        validate_new_reading(
            payload.reading_date,
            payload.value_kwh,
            last.reading_date if last else None,
            float(last.value_kwh) if last else None,
            new_time=reading_time,
            prev_time=last.reading_time if last else None,
        )
    except ReadingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Procedencia de una lectura manual:
    # - observada físicamente AHORA, con hora real -> verified (evidencia directa).
    # - en otro caso -> confirmed (la fecha la confirma el usuario, sin ser
    #   observación física verificada). time_known solo si vino hora real.
    time_known = payload.reading_time is not None
    if payload.observed_now and time_known:
        confidence = "verified"
    else:
        confidence = "confirmed"
    reading = MeterReading(
        reading_date=payload.reading_date,
        reading_time=reading_time,
        value_kwh=payload.value_kwh,
        note=payload.note,
        source="manual",
        date_confidence=confidence,
        time_known=time_known,
    )
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una lectura para esa fecha y hora.",
        )
    db.refresh(reading)

    # Captura del clima del intervalo (lectura anterior -> esta). Es best-effort:
    # la lectura YA está guardada y confirmada arriba. Cualquier problema se
    # traduce a estado persistido (pending/failed) y, si algo inesperado ocurre,
    # se descarta sin afectar la respuesta de la lectura.
    try:
        row = capture_latest_interval(db, reading)
        if row is not None:
            db.commit()
    except Exception:  # noqa: BLE001 - el registro eléctrico nunca debe fallar por el clima
        db.rollback()

    return reading


@router.get("", response_model=list[ReadingOut])
def list_readings(
    db: Session = Depends(get_db),
    start: date | None = Query(None),
    end: date | None = Query(None),
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'start' no puede ser posterior a 'end'.",
        )
    stmt = select(MeterReading).order_by(
        MeterReading.reading_date.asc(), MeterReading.reading_time.asc()
    )
    if start:
        stmt = stmt.where(MeterReading.reading_date >= start)
    if end:
        stmt = stmt.where(MeterReading.reading_date <= end)
    return db.execute(stmt).scalars().all()


@router.patch("/{reading_id}/value", response_model=ReadingOut)
def correct_reading_value(
    reading_id: int, payload: ReadingCorrectionIn, db: Session = Depends(get_db)
):
    """Corrige el valor de una lectura. En una MISMA transacción: cambia el
    value_kwh y registra la corrección en reading_corrections (valor anterior,
    nuevo, motivo). No hay correcciones silenciosas."""
    reading = db.get(MeterReading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada.")

    old = reading.value_kwh
    new = Decimal(str(payload.new_value))
    if new == old:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nuevo valor es igual al actual.",
        )

    db.add(
        ReadingCorrection(
            reading_id=reading.id,
            old_value=old,
            new_value=new,
            reason=payload.reason,
        )
    )
    reading.value_kwh = new
    db.commit()  # cambio + auditoría en la misma transacción
    db.refresh(reading)
    return reading


@router.patch("/{reading_id}/confirm-date", response_model=ReadingOut)
def confirm_reading_date(reading_id: int, db: Session = Depends(get_db)):
    """Confirma la fecha de una lectura pendiente/inferida: sube su
    date_confidence a 'confirmed'. NO toca valor, fecha, hora ni nota.

    Protecciones:
    - Una lectura ya 'verified' NO se degrada ni cambia (409).
    - Una lectura ya 'confirmed' se deja igual (idempotente, 200).
    - Solo 'pending' e 'inferred' se promueven a 'confirmed'.
    """
    reading = db.get(MeterReading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada.")

    if reading.date_confidence == "verified":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La lectura ya está verificada; no se modifica.",
        )
    if reading.date_confidence in ("pending", "inferred"):
        reading.date_confidence = "confirmed"
        db.commit()
        db.refresh(reading)
    # si ya era 'confirmed', no se toca nada
    return reading


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    """Borra una lectura, copiándola antes a deleted_readings (auditoría)."""
    reading = db.get(MeterReading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada.")

    db.add(
        DeletedReading(
            original_id=reading.id,
            reading_date=reading.reading_date,
            reading_time=reading.reading_time,
            value_kwh=reading.value_kwh,
            note=reading.note,
            created_at=reading.created_at,
        )
    )
    db.delete(reading)
    db.commit()
