"""Varias lecturas por día: fecha + hora. Usan el fixture `client` de conftest."""


def _post(client, d, v, t=None, note=None):
    body = {"reading_date": d, "value_kwh": v}
    if t is not None:
        body["reading_time"] = t
    if note is not None:
        body["note"] = note
    return client.post("/api/readings", json=body)


def test_two_readings_same_day_ok(client):
    assert _post(client, "2026-08-26", 2639, "08:00:00").status_code == 201
    assert _post(client, "2026-08-26", 2647, "18:00:00").status_code == 201
    lst = client.get("/api/readings").json()
    assert len(lst) == 2


def test_same_day_ordered_by_time(client):
    _post(client, "2026-08-26", 2647, "18:00:00")  # más tarde, se registra 1º
    # una lectura anterior en el mismo día: hora menor que la última -> rechazada
    r = _post(client, "2026-08-26", 2639, "08:00:00")
    assert r.status_code == 400  # el instante no avanza


def test_duplicate_date_time_rejected(client):
    assert _post(client, "2026-08-26", 2639, "08:00:00").status_code == 201
    # misma fecha y hora exactas -> el instante no es posterior -> 400
    r = _post(client, "2026-08-26", 2650, "08:00:00")
    assert r.status_code == 400


def test_counter_cannot_decrease_same_day(client):
    _post(client, "2026-08-26", 2647, "08:00:00")
    r = _post(client, "2026-08-26", 2640, "18:00:00")  # hora avanza pero valor baja
    assert r.status_code == 400


def test_consumption_between_same_day_readings(client):
    _post(client, "2026-08-26", 2639, "08:00:00")
    _post(client, "2026-08-26", 2647, "18:00:00")
    # consumo intradía: 8 kWh en el mismo día
    s = client.get("/api/analytics/summary").json()
    assert s["total_kwh"] == 8.0


def test_backward_compatible_without_time(client):
    # Sin reading_time: se asume medianoche. Compatibilidad con lecturas viejas.
    r = _post(client, "2026-08-26", 2639)
    assert r.status_code == 201
    assert r.json()["reading_time"] == "00:00:00"


def test_manual_reading_provenance(client):
    # Con hora: source=manual, confirmed, time_known=True.
    r = _post(client, "2026-08-26", 2639, "08:00:00")
    b = r.json()
    assert b["source"] == "manual"
    assert b["date_confidence"] == "confirmed"
    assert b["time_known"] is True


def test_manual_reading_without_time_is_time_unknown(client):
    r = _post(client, "2026-08-26", 2639)  # sin hora
    b = r.json()
    assert b["time_known"] is False
    assert b["date_confidence"] == "confirmed"  # nunca verified automático


def test_correct_reading_value_records_correction(client):
    rid = _post(client, "2026-08-26", 2639, "08:00:00").json()["id"]
    r = client.patch(f"/api/readings/{rid}/value",
                     json={"new_value": 2650, "reason": "ajuste manual"})
    assert r.status_code == 200
    assert r.json()["value_kwh"] == 2650.0


def test_correct_reading_same_value_rejected(client):
    rid = _post(client, "2026-08-26", 2639, "08:00:00").json()["id"]
    r = client.patch(f"/api/readings/{rid}/value", json={"new_value": 2639})
    assert r.status_code == 400


def test_observed_now_with_time_is_verified(client):
    r = client.post("/api/readings", json={
        "reading_date": "2026-08-26", "value_kwh": 2639,
        "reading_time": "08:30:00", "observed_now": True})
    b = r.json()
    assert b["date_confidence"] == "verified"
    assert b["time_known"] is True


def test_observed_now_without_time_is_confirmed(client):
    # observed_now sin hora real NO debe ser verified.
    r = client.post("/api/readings", json={
        "reading_date": "2026-08-26", "value_kwh": 2639,
        "observed_now": True})
    b = r.json()
    assert b["date_confidence"] == "confirmed"
    assert b["time_known"] is False


def test_manual_without_observed_now_is_confirmed(client):
    r = client.post("/api/readings", json={
        "reading_date": "2026-08-26", "value_kwh": 2639,
        "reading_time": "08:30:00"})  # sin observed_now
    assert r.json()["date_confidence"] == "confirmed"


def test_data_quality_endpoint(client):
    _post(client, "2026-08-01", 100, "08:00:00")
    _post(client, "2026-08-05", 140, "08:00:00")  # hueco de 4 días
    q = client.get("/api/analytics/data-quality").json()
    assert q["total_readings"] == 2
    assert q["observed_days"] == 2
    assert q["interpolated_days"] == 3   # 02,03,04 sin lectura
    assert q["time_known_count"] == 2
    assert len(q["irregular_intervals"]) == 1  # intervalo de 4 días


def test_multi_day_and_intraday_mix(client):
    _post(client, "2026-08-26", 2639, "08:00:00")
    _post(client, "2026-08-26", 2647, "18:00:00")  # +8 intradía
    _post(client, "2026-08-27", 2660, "09:00:00")  # +13 al día siguiente
    s = client.get("/api/analytics/summary").json()
    assert s["total_kwh"] == 21.0  # 8 + 13
