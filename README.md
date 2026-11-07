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

## Estado del proyecto

| Área | Estado |
|---|---|
| Backend (FastAPI) | funcional, 52 pruebas verdes |
| Base de datos | Neon PostgreSQL 18.6, migraciones Alembic al día |
| Entornos | `APP_ENV` = development / test / production |
| Frontend (Next.js) | base + dashboard principal |
| Despliegue | pendiente (Render + Vercel) |

## Backend

Requiere **Python 3.12** (el código usa sintaxis `X | Y`).

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # define APP_ENV y DATABASE_URL

# Crear/actualizar las tablas con migraciones
alembic upgrade head

# Verificar la conexión (no imprime la contraseña)
python scripts/check_db.py

# Levantar la API
uvicorn app.main:app --reload
```

Docs de la API en http://127.0.0.1:8000/docs

### Entornos (`APP_ENV`)

- **development** (por defecto): permite SQLite local si no hay `DATABASE_URL`.
- **test**: aislamiento de pruebas (SQLite temporal por test).
- **production**: exige `DATABASE_URL` de PostgreSQL; SQLite queda prohibido y no
  hay fallback silencioso.

Las tablas en PostgreSQL las gestiona **Alembic**. En SQLite (solo pruebas) se
crean solas al arrancar.

### Endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/health` | estado del servicio |
| POST | `/api/readings` | registrar una lectura |
| GET | `/api/readings?start=&end=` | listar lecturas |
| DELETE | `/api/readings/{id}` | borrar (con auditoría en `deleted_readings`) |
| GET | `/api/tariff` | tarifa vigente (solo lectura) |
| PUT | `/api/tariff` | crear / actualizar tarifa |
| GET | `/api/analytics/summary` | consumo, promedio, costo y proyección |

Reglas de negocio clave:
- El contador solo sube; no se admiten dos lecturas el mismo día.
- El consumo se calcula (diferencia entre lecturas), no se guarda duplicado.
- El costo de cada tramo usa la tarifa vigente en su fecha de inicio (tarifas
  históricas). Una tarifa futura nunca se aplica a un tramo anterior.
- Ningún `GET` escribe en la base.
- La proyección mensual es estadística (promedio × 30), **no** Machine Learning.

### Pruebas

```bash
cd backend
pytest          # 52 pruebas
```

## Frontend

Requiere **Node 18+** (probado con Node 24 y Next.js 16).

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev                  # http://localhost:3000
```

Páginas: Dashboard (consume `/api/analytics/summary`), y Lecturas, Tarifas y
Analítica (en construcción). La gráfica histórica está pendiente de un endpoint
de serie temporal en el backend.

## Base de datos — ramas de Neon

- `production`: rama principal.
- `integration`: rama hija para pruebas de integración, sin afectar datos reales.

## Despliegue

- Base de datos: Neon (PostgreSQL).
- Backend: Render. Define `APP_ENV=production` y `DATABASE_URL`.
- Frontend: Vercel. Define `NEXT_PUBLIC_API_URL` con la URL del backend.
- Añade el dominio de Vercel a `CORS_ORIGINS` del backend.

Ver `docs/PLAN.md` para el plan completo por fases.
