from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.invoice import Invoice
from app.schemas.analytics import InvoiceComparisonOut
from app.schemas.invoice import InvoiceCreate, InvoiceOut

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    inv = Invoice(
        period_start=payload.period_start,
        period_end=payload.period_end,
        billed_kwh=payload.billed_kwh,
        billed_amount=payload.billed_amount,
        issued_date=payload.issued_date,
        notes=payload.notes,
    )
    db.add(inv)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una factura para ese período.",
        )
    db.refresh(inv)
    return inv


@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.execute(
        select(Invoice).order_by(Invoice.period_start.asc())
    ).scalars().all()


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    db.delete(inv)
    db.commit()


@router.get("/{invoice_id}/comparison", response_model=InvoiceComparisonOut)
def compare_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Compara el consumo/costo calculado por SmartEnergy ML (para el período
    REAL de la factura, no el mes calendario) contra lo facturado. Las
    diferencias porcentuales devuelven None cuando el denominador es 0."""
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    # import local para no crear ciclos; reutiliza el cálculo por período
    from app.routers.analytics import _period_result

    calc = _period_result(db, inv.period_start, inv.period_end)
    billed_kwh = float(inv.billed_kwh)
    billed_amount = float(inv.billed_amount)

    kwh_diff = round(calc.kwh - billed_kwh, 3)
    cost_diff = round(calc.estimated_cost - billed_amount, 2)
    kwh_pct = round(100 * kwh_diff / billed_kwh, 2) if billed_kwh else None
    cost_pct = round(100 * cost_diff / billed_amount, 2) if billed_amount else None

    return InvoiceComparisonOut(
        period_start=inv.period_start,
        period_end=inv.period_end,
        calculated_kwh=calc.kwh,
        calculated_cost=calc.estimated_cost,
        calculated_sufficient=calc.sufficient,
        calculated_estimated=calc.estimated,
        billed_kwh=billed_kwh,
        billed_amount=billed_amount,
        kwh_diff=kwh_diff,
        kwh_diff_pct=kwh_pct,
        cost_diff=cost_diff,
        cost_diff_pct=cost_pct,
        currency=calc.currency,
        note=calc.note,
    )
