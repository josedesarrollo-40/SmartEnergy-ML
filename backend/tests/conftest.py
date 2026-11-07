"""Fixtures compartidos. Cada test recibe un cliente con su PROPIA base de
datos SQLite en archivo temporal, así no comparten datos entre ejecuciones."""

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Importar modelos para registrarlos en Base.metadata.
from app import models  # noqa: F401


@pytest.fixture()
def client() -> Iterator[TestClient]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        os.unlink(path)
