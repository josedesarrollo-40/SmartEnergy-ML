"""Resolución de la URL de base para Alembic, con reglas por entorno.

Vive en su propio módulo (en vez de dentro de env.py) para poder probarlo sin
disparar la ejecución de migraciones que env.py hace al importarse.
"""

from app.core.config import ConfigError, get_settings


def get_migration_url() -> str:
    """URL para las migraciones. En production exige PostgreSQL y nunca cae a
    SQLite; en development/test usa SQLite como fallback explícito. No imprime
    credenciales."""
    settings = get_settings()
    if settings.is_production:
        url = settings.database_url
        if not url or url.startswith("sqlite"):
            raise ConfigError(
                "APP_ENV=production: las migraciones requieren una DATABASE_URL "
                "de PostgreSQL. No se permite migrar sobre SQLite en producción."
            )
        return url
    return settings.database_url or "sqlite:///./smartenergy_dev.db"
