import math
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.routers import analytics, invoices, readings, tariff

# Importa los modelos para que se registren en Base.metadata.
from app import models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Las tablas en PostgreSQL las gestiona Alembic (alembic upgrade head).
    # Solo con SQLite (pruebas/desarrollo local) creamos las tablas al vuelo,
    # para no obligar a correr migraciones en cada test.
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SmartEnergy ML API",
    description="API REST para registrar, analizar y predecir el consumo "
    "eléctrico residencial.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _clean_non_finite(value):
    """Reemplaza NaN/inf por None en el detalle del error, recursivamente.
    FastAPI mete el valor crudo en 'input'; si es NaN/inf, el JSON estándar no
    lo puede serializar y la respuesta de error reventaría."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _clean_non_finite(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_non_finite(v) for v in value]
    return value


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = _clean_non_finite(jsonable_encoder(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(readings.router)
app.include_router(tariff.router)
app.include_router(analytics.router)
app.include_router(invoices.router)
