"""Integración con Open-Meteo Historical Weather API.

Relaciona el consumo de cada intervalo entre dos lecturas con el clima de ESE
periodo (no con la temperatura del instante de registro).

Principios:
- La consulta se hace SIEMPRE desde el backend, nunca desde el navegador.
- Un fallo de Open-Meteo NO impide registrar la lectura (best-effort).
- Timeout y manejo de errores explícitos.
- Sin datos inventados: si no hay observaciones, los agregados quedan en NULL y
  el estado refleja pendiente/fallido. Nunca se convierten faltantes en ceros.
- Límites temporales sin doble conteo entre intervalos consecutivos:
  el intervalo (A, B] toma las horas estrictamente posteriores a la lectura A y
  hasta la lectura B inclusive. Así una observación pertenece a un solo
  intervalo.

Atribución: datos meteorológicos de Open-Meteo (https://open-meteo.com),
bajo licencia CC BY 4.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

import httpx

from app.core.config import get_settings

SOURCE = "open-meteo"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Open-Meteo archive suele tener ~5 días de retardo. Un intervalo cuyo fin es
# más reciente que esto se deja PENDIENTE (no fallido): se recupera luego.
ARCHIVE_LAG_DAYS = 6


class WeatherUnavailable(Exception):
    """El periodo pedido aún no está disponible en el archivo (muy reciente).
    No es un fallo recuperable por reintento inmediato: queda pendiente."""


class WeatherFetchError(Exception):
    """Error de red/HTTP/timeout al consultar Open-Meteo. Recuperable."""


@dataclass
class WeatherAggregate:
    temp_avg_c: float | None
    temp_max_c: float | None
    temp_min_c: float | None
    humidity_avg_pct: float | None
    observation_count: int


def _period_is_too_recent(end_dt: datetime) -> bool:
    """True si el fin del intervalo es tan reciente que el archivo histórico
    probablemente aún no lo cubre."""
    cutoff = datetime.now().date() - timedelta(days=ARCHIVE_LAG_DAYS)
    return end_dt.date() > cutoff


def fetch_hourly(
    start_day: date, end_day: date, *, client: httpx.Client | None = None
) -> dict[str, list]:
    """Pide a Open-Meteo las series horarias de temperatura y humedad para el
    rango de días [start_day, end_day]. Devuelve el bloque 'hourly' crudo.

    Lanza WeatherFetchError ante cualquier problema de red/HTTP/timeout.
    """
    settings = get_settings()
    params = {
        "latitude": settings.weather_latitude,
        "longitude": settings.weather_longitude,
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "hourly": "temperature_2m,relative_humidity_2m",
        "timezone": settings.weather_timezone,
        "temperature_unit": "celsius",
    }
    owns_client = client is None
    try:
        c = client or httpx.Client(timeout=settings.weather_timeout_seconds)
        try:
            resp = c.get(ARCHIVE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        finally:
            if owns_client:
                c.close()
    except (httpx.HTTPError, ValueError) as exc:  # red, timeout, HTTP, JSON
        raise WeatherFetchError(str(exc)) from exc

    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherFetchError("Respuesta de Open-Meteo sin bloque 'hourly'.")
    return hourly


def aggregate_interval(
    hourly: dict[str, list], start_dt: datetime, end_dt: datetime
) -> WeatherAggregate:
    """Agrega las observaciones horarias dentro del intervalo (start_dt, end_dt].

    Rango semiabierto por la izquierda para no contar dos veces la frontera
    entre intervalos consecutivos. Si no hay observaciones válidas, los
    agregados quedan en None y observation_count = 0 (nunca 0.0 numérico).
    """
    times: list[str] = hourly.get("time", []) or []
    temps: list = hourly.get("temperature_2m", []) or []
    hums: list = hourly.get("relative_humidity_2m", []) or []

    sel_temps: list[float] = []
    sel_hums: list[float] = []
    for i, t in enumerate(times):
        try:
            # Open-Meteo entrega "YYYY-MM-DDTHH:MM" en la zona horaria pedida.
            obs_dt = datetime.fromisoformat(t)
        except ValueError:
            continue
        if obs_dt <= start_dt or obs_dt > end_dt:
            continue  # fuera del rango (start_dt, end_dt]
        temp = temps[i] if i < len(temps) else None
        hum = hums[i] if i < len(hums) else None
        if temp is not None:
            sel_temps.append(float(temp))
        if hum is not None:
            sel_hums.append(float(hum))

    n = max(len(sel_temps), len(sel_hums))
    if n == 0:
        return WeatherAggregate(None, None, None, None, 0)

    temp_avg = round(sum(sel_temps) / len(sel_temps), 1) if sel_temps else None
    temp_max = round(max(sel_temps), 1) if sel_temps else None
    temp_min = round(min(sel_temps), 1) if sel_temps else None
    hum_avg = round(sum(sel_hums) / len(sel_hums), 1) if sel_hums else None
    return WeatherAggregate(temp_avg, temp_max, temp_min, hum_avg, n)


def compute_interval_weather(
    start_dt: datetime, end_dt: datetime, *, client: httpx.Client | None = None
) -> WeatherAggregate:
    """Obtiene y agrega el clima del intervalo (start_dt, end_dt].

    - Lanza WeatherUnavailable si el periodo es demasiado reciente (pendiente).
    - Lanza WeatherFetchError ante errores de red/HTTP/timeout (fallido).
    """
    if end_dt <= start_dt:
        # Intervalo intradía o incoherente: no se consulta clima.
        return WeatherAggregate(None, None, None, None, 0)
    if _period_is_too_recent(end_dt):
        raise WeatherUnavailable(
            f"El periodo hasta {end_dt.date()} aún no está en el archivo histórico."
        )
    hourly = fetch_hourly(start_dt.date(), end_dt.date(), client=client)
    return aggregate_interval(hourly, start_dt, end_dt)


def as_decimal(value: float | None, places: str = "0.1") -> Decimal | None:
    """Convierte a Decimal con 1 decimal, conservando None (no 0)."""
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(places))
