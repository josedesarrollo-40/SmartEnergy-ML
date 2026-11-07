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


def test_multi_day_and_intraday_mix(client):
    _post(client, "2026-08-26", 2639, "08:00:00")
    _post(client, "2026-08-26", 2647, "18:00:00")  # +8 intradía
    _post(client, "2026-08-27", 2660, "09:00:00")  # +13 al día siguiente
    s = client.get("/api/analytics/summary").json()
    assert s["total_kwh"] == 21.0  # 8 + 13
