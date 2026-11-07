"""Pruebas de la API. Cada test usa el fixture `client` de conftest.py, que le
da una base de datos limpia y aislada."""


def _post(client, d, v, note=None):
    body = {"reading_date": d, "value_kwh": v}
    if note is not None:
        body["note"] = note
    return client.post("/api/readings", json=body)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# --- Registro de lecturas -------------------------------------------------

def test_first_reading_ok(client):
    r = _post(client, "2026-01-01", 100.0)
    assert r.status_code == 201
    assert r.json()["value_kwh"] == 100.0


def test_second_valid_reading_ok(client):
    assert _post(client, "2026-01-01", 100.0).status_code == 201
    assert _post(client, "2026-01-11", 150.0).status_code == 201


def test_counter_below_previous_rejected(client):
    _post(client, "2026-01-01", 100.0)
    r = _post(client, "2026-01-11", 90.0)
    assert r.status_code == 400


def test_repeated_date_rejected(client):
    _post(client, "2026-01-01", 100.0)
    # Misma fecha: la validación aplicativa la corta como fecha no posterior.
    r = _post(client, "2026-01-01", 120.0)
    assert r.status_code == 400


def test_earlier_date_rejected(client):
    _post(client, "2026-01-10", 100.0)
    r = _post(client, "2026-01-05", 120.0)
    assert r.status_code == 400


def test_negative_value_rejected(client):
    r = _post(client, "2026-01-01", -5.0)
    assert r.status_code == 422  # lo corta Pydantic (ge=0)


def test_non_finite_value_rejected(client):
    # NaN no es JSON estándar. Lo mandamos como texto crudo (content=) para que
    # el cliente NO intente serializarlo; así llega al servidor y este lo rechaza.
    r = client.post(
        "/api/readings",
        content='{"reading_date": "2026-01-01", "value_kwh": NaN}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code in (400, 422)


# --- Historial y borrado --------------------------------------------------

def test_list_readings(client):
    _post(client, "2026-01-01", 100.0)
    _post(client, "2026-01-11", 150.0)
    listing = client.get("/api/readings").json()
    assert len(listing) == 2


def test_invalid_query_dates(client):
    r = client.get("/api/readings", params={"start": "2026-02-01", "end": "2026-01-01"})
    assert r.status_code == 400


def test_delete_reading_audits(client):
    rid = _post(client, "2026-01-01", 100.0).json()["id"]
    r = client.delete(f"/api/readings/{rid}")
    assert r.status_code == 204
    assert client.get("/api/readings").json() == []


def test_delete_missing_reading(client):
    r = client.delete("/api/readings/9999")
    assert r.status_code == 404


# --- Analítica ------------------------------------------------------------

def test_summary_consumption(client):
    _post(client, "2026-01-01", 100.0)
    _post(client, "2026-01-11", 150.0)   # +50 kWh en 10 días
    data = client.get("/api/analytics/summary").json()
    assert data["total_kwh"] == 50.0
    assert data["avg_daily_kwh"] == 5.0
    assert data["currency"] == "COP"
    assert data["estimated_cost"] == round(50 * 997.92, 2)


# --- Tarifa ---------------------------------------------------------------

def test_tariff_update(client):
    r = client.put("/api/tariff", json={"price_per_kwh": 1000.0, "currency": "COP"})
    assert r.status_code == 200
    assert float(r.json()["price_per_kwh"]) == 1000.0


def test_tariff_non_finite_rejected(client):
    r = client.put(
        "/api/tariff",
        content='{"price_per_kwh": Infinity, "currency": "COP"}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code in (400, 422)
