"""Facturas: CRUD, duplicados, cálculo por período y comparación."""


def _reading(client, d, v, t="08:00:00"):
    return client.post("/api/readings",
                       json={"reading_date": d, "value_kwh": v, "reading_time": t})


def test_create_and_list_invoice(client):
    r = client.post("/api/invoices", json={
        "period_start": "2026-09-01", "period_end": "2026-09-30",
        "billed_kwh": 200, "billed_amount": 200000})
    assert r.status_code == 201
    assert len(client.get("/api/invoices").json()) == 1


def test_duplicate_invoice_period_rejected(client):
    body = {"period_start": "2026-09-01", "period_end": "2026-09-30",
            "billed_kwh": 200, "billed_amount": 200000}
    assert client.post("/api/invoices", json=body).status_code == 201
    assert client.post("/api/invoices", json=body).status_code == 409


def test_invoice_period_order_validated(client):
    r = client.post("/api/invoices", json={
        "period_start": "2026-09-30", "period_end": "2026-09-01",
        "billed_kwh": 200, "billed_amount": 200000})
    assert r.status_code == 422


def test_delete_invoice(client):
    rid = client.post("/api/invoices", json={
        "period_start": "2026-09-01", "period_end": "2026-09-30",
        "billed_kwh": 200, "billed_amount": 200000}).json()["id"]
    assert client.delete(f"/api/invoices/{rid}").status_code == 204
    assert client.delete(f"/api/invoices/{rid}").status_code == 404


def test_monthly_insufficient_without_readings(client):
    q = client.get("/api/analytics/monthly", params={"year": 2026, "month": 9}).json()
    assert q["sufficient"] is False


def test_period_calculation_full_interval(client):
    # Dos lecturas que cubren todo septiembre: tramo completo, no estimado.
    _reading(client, "2026-09-01", 100)
    _reading(client, "2026-10-01", 160)  # +60 en 30 días
    q = client.get("/api/analytics/period",
                   params={"start": "2026-09-01", "end": "2026-10-01"}).json()
    assert q["sufficient"] is True
    assert q["kwh"] == 60.0


def test_period_interpolation_marked_estimated(client):
    # El rango cae PARCIALMENTE dentro de un tramo -> estimado.
    _reading(client, "2026-09-01", 100)
    _reading(client, "2026-10-01", 160)  # 60 kWh en 30 días = 2/día
    # pedimos solo 10 días: 2026-09-01..2026-09-11 -> ~20 kWh, estimado
    q = client.get("/api/analytics/period",
                   params={"start": "2026-09-01", "end": "2026-09-11"}).json()
    assert q["sufficient"] is True
    assert q["estimated"] is True
    assert q["estimated_fraction"] > 0


def test_invoice_comparison(client):
    _reading(client, "2026-09-01", 100)
    _reading(client, "2026-10-01", 160)  # 60 kWh calculado para septiembre
    inv = client.post("/api/invoices", json={
        "period_start": "2026-09-01", "period_end": "2026-10-01",
        "billed_kwh": 55, "billed_amount": 50000}).json()
    cmp = client.get(f"/api/invoices/{inv['id']}/comparison").json()
    assert cmp["calculated_kwh"] == 60.0
    assert cmp["billed_kwh"] == 55.0
    assert cmp["kwh_diff"] == 5.0
    assert cmp["kwh_diff_pct"] is not None


def test_invoice_comparison_no_divide_by_zero(client):
    _reading(client, "2026-09-01", 100)
    _reading(client, "2026-10-01", 160)
    inv = client.post("/api/invoices", json={
        "period_start": "2026-09-01", "period_end": "2026-10-01",
        "billed_kwh": 0, "billed_amount": 0}).json()
    cmp = client.get(f"/api/invoices/{inv['id']}/comparison").json()
    assert cmp["kwh_diff_pct"] is None   # billed_kwh = 0
    assert cmp["cost_diff_pct"] is None  # billed_amount = 0
