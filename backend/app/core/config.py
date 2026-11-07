from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída desde variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos. Vacío por defecto para permitir arranque/tests sin Neon.
    database_url: str = ""

    # Tarifa por defecto.
    default_currency: str = "COP"
    default_price_per_kwh: float = 997.92

    # CORS: lista separada por comas.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
