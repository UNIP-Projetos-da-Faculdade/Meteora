from collections.abc import Iterator
import os

import mongomock
import pytest
from fastapi.testclient import TestClient

# A configuração dos testes não depende do .env do desenvolvedor.
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017")
os.environ.setdefault("MONGODB_DATABASE", "meteora_test")

from app.config import Settings
from app.main import create_app


@pytest.fixture
def database() -> mongomock.database.Database:
    return mongomock.MongoClient(tz_aware=True).meteora_test


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, database: mongomock.database.Database) -> Iterator[TestClient]:
    monkeypatch.setattr("app.main.MongoClient", lambda *args, **kwargs: database.client)
    settings = Settings(_env_file=None, mongodb_database=database.name)
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def payload() -> dict[str, float]:
    return {"temperatura": 27.5, "umidade": 65.2, "pressao": 1013.25, "luminosidade": 350.8}
