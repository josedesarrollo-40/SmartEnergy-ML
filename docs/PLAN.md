# Plan de SmartEnergy ML

## Arquitectura

```
Navegador (Next.js)  --HTTPS/REST-->  FastAPI  --SQLAlchemy-->  Neon PostgreSQL
     Vercel                            Render                      Neon
```

El frontend solo habla con la API REST. El backend es la única puerta a la base
de datos. Los secretos viven solo en el backend (variables de entorno).

## Base de datos (MVP)

| Tabla | Para qué |
|---|---|
| `meter_readings` | Cada lectura del contador (valor acumulado en kWh). |
| `tariffs` | Tarifa por kWh, con historial (vigente = valid_from más reciente). |

El consumo entre dos lecturas se **calcula** (diferencia de valores acumulados),
no se guarda. Regla: el contador solo sube; una lectura nueva no puede tener
valor menor ni fecha anterior o igual a la última.

## Endpoints

```
GET    /health
POST   /api/readings
GET    /api/readings?start=&end=
DELETE /api/readings/{id}
GET    /api/tariff
PUT    /api/tariff
GET    /api/analytics/summary
```

Pendientes en fases siguientes: `/api/analytics/history`, `/api/predictions`.

## Fases

1. **Base** (hecho y probado) — monorepo, backend FastAPI, modelos, servicios de cálculo, tests. ✅
   - Auditoría aplicada: Numeric en kWh y dinero, UNIQUE de fecha, rechazo de NaN/infinito,
     validación de fechas de consulta, DELETE con auditoría (`deleted_readings`), costo por
     tarifa histórica, `lifespan` en vez de `on_event`, tests aislados por caso.
   - 27 pruebas pasan. App probada end-to-end sobre SQLite (health, alta, duplicado, resumen).
2. **Neon** — conectar a PostgreSQL real, probar end-to-end.
3. **Frontend** — Next.js: dashboard, formulario de lectura, historial, gráficas.
4. **Análisis** — historial por día/semana/mes, comparación de periodos, proyección estadística.
5. **ML** — modelo predictivo + métricas. Solo con datos suficientes. Marcado como ML, distinto de la estimación estadística.
6. **Deploy** — Neon + Render (backend) + Vercel (frontend), CORS.

## Estimación estadística vs ML

Hasta tener historial real suficiente, la proyección que ve el usuario es
**estadística** (promedio diario × 30), con `method = "statistical"`. El ML llega
en la fase 5 con evaluación de desempeño. Nunca se presenta un modelo como
confiable sin datos y métricas.

## Entorno

- **Python 3.12** (el código usa sintaxis `X | Y`, no corre en 3.9). En la Mac se instaló
  con `brew install python@3.12`.
- Las pruebas se corren con solo las dependencias necesarias (sin pandas ni scikit-learn,
  que entran en la fase 5 de ML).

## Pruebas

- `backend/tests/test_consumption.py` — cálculo de kWh, costo, tarifa histórica, validación (puras).
- `backend/tests/test_api.py` — endpoints sobre base SQLite aislada por test (via `conftest.py`).
- Casos cubiertos: primera lectura, lectura válida, contador que baja, fecha repetida, fecha
  anterior, valor negativo, valor no finito, consumo entre lecturas, borrado, cambio de tarifa,
  tarifa histórica, fechas de consulta inválidas, resumen.
- Correr:
  ```bash
  cd backend
  python3.12 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  pytest
  ```
- Estado: **27 pruebas pasan**.

## Despliegue — resumen

- Neon: crear proyecto, copiar `DATABASE_URL` al `.env` del backend y a Render.
- Render: servicio web Python, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Vercel: proyecto Next.js, `NEXT_PUBLIC_API_URL` = URL de Render.
- CORS: añadir el dominio de Vercel a `CORS_ORIGINS`.
- Secretos nunca en GitHub (`.env` en `.gitignore`).
