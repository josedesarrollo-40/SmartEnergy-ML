# Migraciones (Alembic)

La base de datos se crea y evoluciona con migraciones, no con `create_all`.

## Comandos

Desde `backend/`, con el entorno activo y `DATABASE_URL` definida:

```bash
# Aplicar todas las migraciones (crea/actualiza las tablas)
alembic upgrade head

# Crear una migración nueva tras cambiar los modelos
alembic revision --autogenerate -m "descripcion del cambio"

# Volver una migración atrás
alembic downgrade -1

# Ver el estado actual
alembic current
```

La URL se lee de `DATABASE_URL` (entorno). Nunca se escribe en `alembic.ini`.
Sin `DATABASE_URL`, usa la SQLite de desarrollo.
