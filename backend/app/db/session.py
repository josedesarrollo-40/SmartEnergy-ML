from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import ConfigError, get_settings

settings = get_settings()


def resolve_database_url(settings) -> str:
    """URL de base según el entorno, sin fallbacks silenciosos.

    - production: usa DATABASE_URL (ya validada en config: existe y no es
      SQLite). Si por lo que sea faltara, falla claro.
    - development/test: usa DATABASE_URL si está; si no, SQLite local explícito.
    """
    if settings.is_production:
        if not settings.database_url or settings.database_url.startswith("sqlite"):
            raise ConfigError(
                "En production se requiere una DATABASE_URL de PostgreSQL."
            )
        return settings.database_url

    # development / test: SQLite como fallback explícito de desarrollo.
    return settings.database_url or "sqlite:///./smartenergy_dev.db"


_url = resolve_database_url(settings)

# connect_args solo aplica a SQLite.
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: abre una sesión por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
