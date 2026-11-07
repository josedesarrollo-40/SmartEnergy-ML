from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Si no hay DATABASE_URL (tests locales), caemos a SQLite en memoria de archivo.
_url = settings.database_url or "sqlite:///./smartenergy_dev.db"

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
