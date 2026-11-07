from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reading import DeletedReading, MeterReading
from app.schemas.reading import ReadingCreate, ReadingOut
from app.services.validation import ReadingValidationError, validate_new_reading

router = APIRouter(prefix="/api/readings", tags=["readings"])


@router.post("", response_model=ReadingOut, status_code=status.HTTP_201_CREATED)
def create_reading(payload: ReadingCreate, db: Session = Depends(get_db)):
    """Registra una lectura. Valida contra la última registrada.

    La validación aplicativa y la restricción UNIQUE de la base se complementan:
    la UNIQUE protege contra dos POST simultáneos que pasen la validación a la
    vez (condición de carrera)."""
    last = db.execute(
        select(MeterReading)
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
    ).scalars().first()

    try:
        validate_new_reading(
            payload.reading_date,
            payload.value_kwh,
            last.reading_date if last else None,
            float(last.value_kwh) if last else None,
        )
    except ReadingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    reading = MeterReading(
        reading_date=payload.reading_date,
        value_kwh=payload.value_kwh,
        note=payload.note,
    )
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        # La UNIQUE de reading_date la disparó: ya existe una lectura ese día.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una lectura para esa fecha.",
        )
    db.refresh(reading)
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
    stmt = select(MeterReading).order_by(MeterReading.reading_date.asc())
    if start:
        stmt = stmt.where(MeterReading.reading_date >= start)
    if end:
        stmt = stmt.where(MeterReading.reading_date <= end)
    return db.execute(stmt).scalars().all()


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    """Borra una lectura, copiándola antes a la tabla de auditoría
    deleted_readings (estrategia A2). Ambas operaciones en una transacción."""
    reading = db.get(MeterReading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada.")

    db.add(
        DeletedReading(
            original_id=reading.id,
            reading_date=reading.reading_date,
            value_kwh=reading.value_kwh,
            note=reading.note,
            created_at=reading.created_at,
        )
    )
    db.delete(reading)
    db.commit()
