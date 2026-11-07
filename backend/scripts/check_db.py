"""Verifica la conexión a la base de datos definida en DATABASE_URL.

Uso (desde backend/, con el entorno activo y .env con DATABASE_URL):
    python scripts/check_db.py

No imprime la contraseña. Solo dice si conecta, qué motor es y qué tablas hay.
"""

import sys

from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings


def main() -> int:
    url = get_settings().database_url
    if not url:
        print("DATABASE_URL no está definida. Define Neon en .env primero.")
        return 1

    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            dialect = conn.dialect.name
            version = conn.execute(text("SELECT version()")).scalar() \
                if dialect == "postgresql" else dialect
        tables = sorted(inspect(engine).get_table_names())
        print(f"Conexión OK. Motor: {dialect}")
        print(f"Servidor: {version}")
        print(f"Tablas: {tables or '(ninguna todavía — corre alembic upgrade head)'}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"No se pudo conectar: {type(exc).__name__}: {exc}")
        return 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
