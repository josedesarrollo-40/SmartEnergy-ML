"""Pruebas de las reglas de configuración por entorno (APP_ENV).

Construyen Settings con valores explícitos (no leen el .env real) y comprueban
que la validación falla o pasa según el entorno. No tocan ninguna base real.
"""

import pytest

from app.core.config import ConfigError, Settings, validate_database_config

PG_URL = "postgresql+psycopg2://u:p@host.neon.tech/db?sslmode=require"
SQLITE_URL = "sqlite:///./dev.db"


def _settings(**kw) -> Settings:
    # _env_file=None evita leer el .env del disco en las pruebas.
    return Settings(_env_file=None, **kw)


def test_production_sin_database_url_falla():
    s = _settings(app_env="production", database_url="")
    with pytest.raises(ConfigError):
        validate_database_config(s)


def test_production_con_sqlite_falla():
    s = _settings(app_env="production", database_url=SQLITE_URL)
    with pytest.raises(ConfigError):
        validate_database_config(s)


def test_production_con_postgres_ok():
    s = _settings(app_env="production", database_url=PG_URL)
    validate_database_config(s)  # no lanza
    assert s.is_production is True


def test_development_con_sqlite_ok():
    s = _settings(app_env="development", database_url=SQLITE_URL)
    validate_database_config(s)  # no lanza


def test_development_sin_url_ok():
    s = _settings(app_env="development", database_url="")
    validate_database_config(s)  # no lanza; el fallback SQLite lo da session.py


def test_test_env_sin_url_ok():
    s = _settings(app_env="test", database_url="")
    validate_database_config(s)  # no lanza


def test_resolve_url_production_rechaza_sqlite():
    from app.db.session import resolve_database_url
    s = _settings(app_env="production", database_url=SQLITE_URL)
    with pytest.raises(ConfigError):
        resolve_database_url(s)


def test_resolve_url_development_cae_a_sqlite():
    from app.db.session import resolve_database_url
    s = _settings(app_env="development", database_url="")
    assert resolve_database_url(s).startswith("sqlite")


def test_migrations_production_rechaza_sqlite(monkeypatch):
    """migrations.url.get_migration_url debe fallar en production con SQLite."""
    import migrations.url as murl

    s = _settings(app_env="production", database_url=SQLITE_URL)
    monkeypatch.setattr(murl, "get_settings", lambda: s)
    with pytest.raises(ConfigError):
        murl.get_migration_url()


def test_migrations_production_con_postgres_ok(monkeypatch):
    import migrations.url as murl

    s = _settings(app_env="production", database_url=PG_URL)
    monkeypatch.setattr(murl, "get_settings", lambda: s)
    assert murl.get_migration_url() == PG_URL
