from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Configuración leída desde variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Entorno de la aplicación. Controla las reglas de base de datos.
    # development (por defecto) permite SQLite; production exige PostgreSQL;
    # test conserva el aislamiento de las pruebas.
    app_env: AppEnv = "development"

    # Base de datos. Vacío por defecto para permitir arranque/tests sin Neon.
    database_url: str = ""

    # Tarifa por defecto.
    default_currency: str = "COP"
    default_price_per_kwh: float = 997.92

    # Ubicación climática de la vivienda (Open-Meteo). Centralizada aquí, NO en
    # .env, y ajustable después para mayor precisión. Inicial: Ibagué, Tolima.
    # No se consulta ni almacena clima de otras ciudades.
    weather_latitude: float = 4.4389
    weather_longitude: float = -75.2322
    weather_timezone: str = "America/Bogota"
    # Segundos de timeout para la consulta a Open-Meteo. Un fallo nunca debe
    # impedir registrar la lectura eléctrica.
    weather_timeout_seconds: float = 10.0

    # CORS: lista separada por comas.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


class ConfigError(RuntimeError):
    """Configuración de entorno inválida o incompleta."""


def validate_database_config(settings: "Settings") -> None:
    """Valida las reglas de base de datos según el entorno. Falla temprano y
    con un mensaje claro, sin fallbacks silenciosos.

    - production: DATABASE_URL obligatoria y NO puede ser SQLite.
    - development/test: SQLite permitido (fallback explícito).
    """
    if settings.is_production:
        if not settings.database_url:
            raise ConfigError(
                "APP_ENV=production requiere DATABASE_URL (PostgreSQL de Neon). "
                "No se define por defecto para no caer a SQLite en silencio."
            )
        if settings.database_url.startswith("sqlite"):
            raise ConfigError(
                "APP_ENV=production no admite SQLite. Usa una DATABASE_URL de "
                "PostgreSQL (Neon)."
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    validate_database_config(settings)
    return settings
