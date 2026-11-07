# SmartEnergy ML

Plataforma web para registrar, analizar y predecir el consumo eléctrico de una vivienda.

## Arquitectura

```
Navegador (Next.js)  --HTTPS/REST-->  FastAPI  --SQLAlchemy-->  Neon PostgreSQL
     Vercel                            Render                      Neon
```

- **frontend/** — Next.js + TypeScript + Tailwind + shadcn/ui + Recharts. Solo habla con la API.
- **backend/** — FastAPI. Única puerta a los datos. Calcula consumo, costo y predicciones.
- **docs/** — documentación del proyecto.

El frontend nunca toca la base de datos. Los secretos viven solo en el backend.

## Backend

Requiere **Python 3.12** (el código usa sintaxis `X | Y`).

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # pon aquí tu DATABASE_URL de Neon

# Crear/actualizar las tablas con migraciones
alembic upgrade head

# Verificar la conexión (no imprime la contraseña)
python scripts/check_db.py

# Levantar la API
uvicorn app.main:app --reload
```

Docs de la API en http://127.0.0.1:8000/docs

Las tablas en PostgreSQL las gestiona **Alembic**. En SQLite (solo pruebas) se
crean solas al arrancar.

## Frontend

Pendiente (fase 4).

## Despliegue

- Base de datos: Neon (PostgreSQL).
- Backend: Render.
- Frontend: Vercel.

Ver `docs/` para el plan completo.
