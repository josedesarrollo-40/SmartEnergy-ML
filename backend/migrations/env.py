"""Entorno de Alembic.

La URL de la base se toma de la variable de entorno DATABASE_URL (nunca del
alembic.ini), para no exponer credenciales. Si no está definida, cae a la misma
SQLite de desarrollo que usa la app.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base

# Importa los modelos para que Base.metadata los conozca (autogenerate).
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogenerate.
target_metadata = Base.metadata


def _get_url() -> str:
    url = get_settings().database_url
    return url or "sqlite:///./smartenergy_dev.db"


def run_migrations_offline() -> None:
    """Migraciones en modo 'offline' (genera SQL sin conectar)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,  # necesario para ALTER en SQLite
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migraciones en modo 'online' (conecta a la base real)."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=is_sqlite,  # batch solo en SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
